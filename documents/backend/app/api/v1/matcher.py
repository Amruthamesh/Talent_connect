from typing import List, AsyncGenerator
from pathlib import Path
import json
import io
import zipfile

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.permissions import require_permission
from app.core.auth import get_current_active_user
from app.db.session import get_db
from app.models.matcher import CandidateProfile, ResumeUpload
from app.schemas.matcher import CandidateProfileResponse, DownloadZipRequest
from app.services.ai.profile_matcher import process_resume_upload
from app.models.user import User

router = APIRouter(prefix="/matcher", tags=["Profile Matcher"])


def format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/upload")
async def upload_and_stream(
    job_description: str = Form(...),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("jobs.matcher.use")),
):
    """
    Upload multiple resumes and stream AI evaluation results (SSE).
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    upload_dir = Path(settings.UPLOAD_DIR)
    # Read files into memory upfront to avoid closed file handles during streaming
    payloads = []
    for f in files:
        payloads.append(
            {
                "filename": f.filename,
                "content_type": f.content_type or "application/octet-stream",
                "bytes": await f.read(),
            }
        )

    async def event_stream() -> AsyncGenerator[bytes, None]:
        for payload in payloads:
            upload_row = ResumeUpload(
                original_filename=payload["filename"],
                stored_path="",
                mime_type=payload["content_type"],
                status="uploaded",
            )
            db.add(upload_row)
            await db.flush()
            try:
                result = await process_resume_upload(payload["bytes"], payload["filename"], upload_dir, job_description)
                upload_row.stored_path = result["stored_path"]
                upload_row.status = "completed"
                upload_row.processed_at = upload_row.uploaded_at
                await db.commit()
                result["upload_id"] = upload_row.id
                yield format_sse("update", result).encode()
            except Exception as exc:
                upload_row.status = "failed"
                upload_row.error_message = str(exc)
                await db.commit()
                yield format_sse("error", {"file": payload["filename"], "message": str(exc)}).encode()
        yield format_sse("done", {}).encode()

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/candidate/{candidate_id}", response_model=CandidateProfileResponse)
async def get_candidate_profile(
    candidate_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve parsed candidate profile."""
    stmt = (
        select(CandidateProfile)
        .options(selectinload(CandidateProfile.upload))
        .where(CandidateProfile.id == candidate_id)
    )
    result = await db.execute(stmt)
    candidate = result.scalars().first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    uploaded_at = candidate.upload.uploaded_at if candidate.upload else None
    payload = CandidateProfileResponse(
        id=candidate.id,
        full_name=candidate.full_name,
        email=candidate.email,
        phone=candidate.phone,
        summary=candidate.summary,
        skills=candidate.skills,
        experiences=candidate.experiences,
        education=candidate.education,
        raw_text=candidate.raw_text,
        uploaded_at=uploaded_at,
    )
    return payload


@router.post("/download-zip")
async def download_selected_resumes(
    request: DownloadZipRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("jobs.matcher.use")),
):
    """Download selected resumes (by upload id) as a ZIP."""
    if not request.candidate_ids:
        raise HTTPException(status_code=400, detail="candidate_ids is required")

    stmt = (
        select(ResumeUpload)
        .where(ResumeUpload.id.in_(request.candidate_ids))
    )
    result = await db.execute(stmt)
    uploads = result.scalars().all()

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for upload in uploads:
            if not upload.stored_path:
                continue
            path = Path(upload.stored_path)
            if not path.exists():
                continue
            arcname = upload.original_filename or f"resume_{upload.id}{path.suffix}"
            try:
                zf.write(path, arcname=arcname)
            except FileNotFoundError:
                continue
    memory_file.seek(0)
    return StreamingResponse(
        memory_file,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="selected_resumes.zip"'},
    )
