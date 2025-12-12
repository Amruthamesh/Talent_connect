import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import Interview
from app.schemas.interview import (
    InterviewCreate,
    InterviewOut,
    FeedbackCreate,
    QuestionCreate,
    ResponseCreate,
)


def _generate_key(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


async def list_interviews(db: AsyncSession) -> List[Interview]:
    result = await db.execute(select(Interview).order_by(Interview.created_at.desc()))
    return result.scalars().all()


async def get_interview(db: AsyncSession, interview_id: int) -> Optional[Interview]:
    result = await db.execute(select(Interview).where(Interview.id == interview_id))
    return result.scalar_one_or_none()


async def get_interview_by_key(db: AsyncSession, key: str) -> Optional[Interview]:
    result = await db.execute(
        select(Interview).where(
            (Interview.interviewer_key == key) | (Interview.candidate_key == key)
        )
    )
    return result.scalar_one_or_none()


async def create_interview(db: AsyncSession, payload: InterviewCreate) -> Interview:
    interview = Interview(
        candidate_name=payload.candidate_name,
        candidate_email=payload.candidate_email,
        role=payload.role,
        company=payload.company,
        round_type=payload.round_type,
        scheduled_at=payload.scheduled_at,
        status="scheduled",
        interviewer_key=_generate_key("interviewer"),
        candidate_key=_generate_key("candidate"),
        notes=payload.notes,
        resume_filename=payload.resume_filename,
        jd_filename=payload.jd_filename,
        jd_text=payload.jd_text,
        transcript=[],
    )
    db.add(interview)
    await db.flush()
    await db.refresh(interview)
    return interview


async def update_status(db: AsyncSession, interview: Interview, status: str) -> Interview:
    interview.status = status
    interview.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(interview)
    return interview


async def add_question(db: AsyncSession, interview: Interview, payload: QuestionCreate) -> Interview:
    transcript = interview.transcript or []
    question_id = f"q-{uuid.uuid4().hex[:8]}"
    transcript.append({"id": question_id, "question": payload.question, "answer": None})
    interview.transcript = transcript
    interview.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(interview)
    return interview


async def add_response(db: AsyncSession, interview: Interview, payload: ResponseCreate) -> Interview:
    transcript = interview.transcript or []
    updated = []
    for item in transcript:
        if item.get("id") == payload.question_id:
            updated.append({**item, "answer": payload.answer})
        else:
            updated.append(item)
    interview.transcript = updated
    interview.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(interview)
    return interview


async def save_feedback(db: AsyncSession, interview: Interview, payload: FeedbackCreate) -> Interview:
    interview.feedback_rating = payload.rating
    interview.feedback_decision = payload.decision
    interview.feedback_comments = payload.comments
    interview.feedback_notes = payload.notes
    interview.status = "completed"
    interview.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(interview)
    return interview
