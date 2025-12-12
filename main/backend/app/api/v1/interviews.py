from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.core.auth import get_current_active_user
from app.core.permissions import require_permission
from app.models.user import User
from app.db.session import get_db
from app.schemas.interview import (
    InterviewCreate,
    InterviewOut,
    InterviewUpdateStatus,
    QuestionCreate,
    ResponseCreate,
    FeedbackCreate,
    ResolveOut,
)
from app.services import interview_service
from app.services.ws_manager import manager
from app.db.session import AsyncSessionLocal
from app.utils.storage import save_upload_file
from app.utils.resume_parser import extract_text
from app.utils.ai_detection import check_resume_for_ai
from pathlib import Path
from app.config import settings


router = APIRouter(prefix="/interviews", tags=["Interviews"])


def _build_interview_out(interview):
    payload = interview.to_dict()
    return InterviewOut(**payload)


@router.get("/", response_model=List[InterviewOut])
async def list_interviews(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("interviews.dashboard"))
):
    interviews = await interview_service.list_interviews(db)
    return [_build_interview_out(i) for i in interviews]


@router.post("/schedule", response_model=InterviewOut)
async def schedule_interview(
    candidate_name: str = Form(...),
    candidate_email: Optional[str] = Form(None),
    role: str = Form(...),
    company: Optional[str] = Form(None),
    round_type: str = Form(...),
    date: str = Form(...),
    time: str = Form(...),
    notes: Optional[str] = Form(None),
    jd_text: Optional[str] = Form(None),
    resume: Optional[UploadFile] = File(None),
    job_description: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("interviews.schedule"))
):
    """Schedule a new interview and generate participant keys."""
    resume_filename = await save_upload_file(resume) if resume else None
    jd_filename = await save_upload_file(job_description) if job_description else None

    # AI Detection: Check if resume is AI-generated
    ai_detection_result = None
    if resume_filename:
        try:
            resume_path = Path(settings.UPLOAD_DIR) / resume_filename
            if resume_path.exists():
                resume_text = extract_text(resume_path)
                ai_detection_result = check_resume_for_ai(resume_text)
        except Exception as e:
            print(f"Error during AI detection: {str(e)}")
            # Continue even if detection fails - don't block the interview creation

    scheduled_str = f"{date} {time}"
    scheduled_at = datetime.fromisoformat(scheduled_str)

    payload = InterviewCreate(
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        role=role,
        company=company,
        round_type=round_type,
        scheduled_at=scheduled_at,
        notes=notes,
        resume_filename=resume_filename,
        jd_filename=jd_filename,
        jd_text=jd_text,
    )

    interview = await interview_service.create_interview(db, payload)
    interview_out = _build_interview_out(interview)
    
    # Add AI detection result to response
    if ai_detection_result:
        interview_out.ai_detection = ai_detection_result
    
    return interview_out


@router.get("/{interview_id}", response_model=InterviewOut)
async def get_interview(
    interview_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    interview = await interview_service.get_interview(db, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return _build_interview_out(interview)


@router.put("/{interview_id}/status", response_model=InterviewOut)
async def update_status(
    interview_id: int,
    payload: InterviewUpdateStatus,
    key: str = Query(..., description="Interviewer key to authorize status changes"),
    db: AsyncSession = Depends(get_db)
):
    interview = await interview_service.get_interview(db, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if interview.interviewer_key != key:
        raise HTTPException(status_code=403, detail="Invalid interviewer key")
    updated = await interview_service.update_status(db, interview, payload.status)
    return _build_interview_out(updated)


@router.post("/{interview_id}/questions", response_model=InterviewOut)
async def send_question(
    interview_id: int,
    payload: QuestionCreate,
    key: str = Query(..., description="Interviewer key to authorize questions"),
    db: AsyncSession = Depends(get_db)
):
    interview = await interview_service.get_interview(db, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if interview.interviewer_key != key:
        raise HTTPException(status_code=403, detail="Invalid interviewer key")
    updated = await interview_service.add_question(db, interview, payload)
    return _build_interview_out(updated)


@router.post("/{interview_id}/responses", response_model=InterviewOut)
async def submit_response(
    interview_id: int,
    payload: ResponseCreate,
    key: str = Query(..., description="Candidate key to authorize responses"),
    db: AsyncSession = Depends(get_db)
):
    interview = await interview_service.get_interview(db, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if interview.candidate_key != key:
        raise HTTPException(status_code=403, detail="Invalid candidate key")
    updated = await interview_service.add_response(db, interview, payload)
    return _build_interview_out(updated)


@router.post("/{interview_id}/feedback", response_model=InterviewOut)
async def submit_feedback(
    interview_id: int,
    payload: FeedbackCreate,
    key: str = Query(..., description="Interviewer key to submit feedback"),
    db: AsyncSession = Depends(get_db)
):
    interview = await interview_service.get_interview(db, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if interview.interviewer_key != key:
        raise HTTPException(status_code=403, detail="Invalid interviewer key")
    updated = await interview_service.save_feedback(db, interview, payload)
    return _build_interview_out(updated)


@router.get("/resolve/key", response_model=ResolveOut)
async def resolve_by_key(
    key: str,
    db: AsyncSession = Depends(get_db)
):
    """Resolve a join key to interview + role for lobby/session access."""
    interview = await interview_service.get_interview_by_key(db, key)
    if not interview:
        raise HTTPException(status_code=404, detail="Invalid key")
    role = "interviewer" if interview.interviewer_key == key else "candidate"
    return ResolveOut(role=role, interview=_build_interview_out(interview))


@router.websocket("/{interview_id}/ws")
async def interview_socket(websocket: WebSocket, interview_id: int, key: str):
    # new session for websocket
    db: AsyncSession = AsyncSessionLocal()
    try:
        interview = await interview_service.get_interview(db, interview_id)
        if not interview:
            await websocket.close(code=4004)
            return
        if key not in [interview.interviewer_key, interview.candidate_key]:
            await websocket.close(code=4003)
            return
        role = "interviewer" if interview.interviewer_key == key else "candidate"
        await manager.connect(interview_id, websocket, role)
        await websocket.send_json({"type": "connected", "role": role})

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            # interviewer sends question
            if msg_type == "question" and role == "interviewer":
                question_text = data.get("question", "").strip()
                if not question_text:
                    continue
                interview = await interview_service.add_question(
                    db, interview, QuestionCreate(question=question_text)
                )
                await db.commit()
                await db.refresh(interview)
                new_question = interview.transcript[-1] if interview.transcript else None
                await manager.broadcast(
                    interview_id,
                    {"type": "question", "interview_id": interview_id, "question": new_question},
                )

            # candidate sends response
            elif msg_type == "response" and role == "candidate":
                question_id = data.get("question_id")
                answer = data.get("answer", "")
                if not question_id or answer is None:
                    continue
                interview = await interview_service.add_response(
                    db, interview, ResponseCreate(question_id=question_id, answer=answer)
                )
                await db.commit()
                await db.refresh(interview)
                await manager.broadcast(
                    interview_id,
                    {
                        "type": "response",
                        "interview_id": interview_id,
                        "question_id": question_id,
                        "answer": answer,
                    },
                )

            # interviewer can mark completed
            elif msg_type == "status" and role == "interviewer":
                status = data.get("status")
                if status:
                    interview = await interview_service.update_status(db, interview, status)
                    await db.commit()
                    await db.refresh(interview)
                    await manager.broadcast(
                        interview_id,
                        {"type": "status", "interview_id": interview_id, "status": status},
                    )

    except WebSocketDisconnect:
        manager.disconnect(interview_id, websocket)
    finally:
        await db.close()


@router.post("/check-resume-ai")
async def check_resume_for_ai_generation(
    resume: UploadFile = File(...),
    current_user: User = Depends(require_permission("interviews.schedule"))
):
    """
    Check if an uploaded resume is AI-generated.
    
    **Required Permission:** `interviews.schedule`
    
    Returns:
    {
        "is_ai_generated": bool,
        "confidence_score": float (0-100),
        "risk_level": str ("high", "medium", "low"),
        "indicators": List of specific AI indicators found,
        "explanation": str,
        "detailed_analysis": Dict with individual scoring components
    }
    """
    try:
        # Save and analyze the resume
        resume_path = None
        try:
            resume_filename = await save_upload_file(resume)
            if resume_filename:
                resume_path = Path(settings.UPLOAD_DIR) / resume_filename
                
                if resume_path.exists():
                    # Extract text from the resume
                    resume_text = extract_text(resume_path)
                    
                    # Run AI detection
                    detection_result = check_resume_for_ai(resume_text)
                    
                    return detection_result
                else:
                    raise HTTPException(status_code=400, detail="Failed to save resume file")
            else:
                raise HTTPException(status_code=400, detail="No resume file provided")
        finally:
            # Clean up temporary file if needed
            if resume_path and resume_path.exists():
                try:
                    resume_path.unlink()
                except:
                    pass
                    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing resume: {str(e)}"
        )
