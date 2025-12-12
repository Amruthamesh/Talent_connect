from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, DateTime, Integer, JSON, Text, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    must_have_skills: Mapped[List[str]] = mapped_column(JSON, default=list)
    preferred_skills: Mapped[List[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ResumeUpload(Base):
    __tablename__ = "resume_uploads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="uploaded", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(String(500))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    candidate_profile: Mapped["CandidateProfile"] = relationship(
        "CandidateProfile", back_populates="upload", uselist=False
    )


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    upload_id: Mapped[int] = mapped_column(ForeignKey("resume_uploads.id"))
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    summary: Mapped[Optional[str]] = mapped_column(Text)
    skills: Mapped[List[str]] = mapped_column(JSON, default=list)
    experiences: Mapped[List[dict]] = mapped_column(JSON, default=list)
    education: Mapped[List[dict]] = mapped_column(JSON, default=list)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    upload: Mapped[ResumeUpload] = relationship("ResumeUpload", back_populates="candidate_profile")
    match_results: Mapped[List["MatchResult"]] = relationship("MatchResult", back_populates="candidate")


class MatchRun(Base):
    __tablename__ = "match_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    job_description: Mapped[str] = mapped_column(Text, nullable=False)
    must_have_skills: Mapped[List[str]] = mapped_column(JSON, default=list)
    preferred_skills: Mapped[List[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(50), default="completed", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    results: Mapped[List["MatchResult"]] = relationship("MatchResult", back_populates="run")


class MatchResult(Base):
    __tablename__ = "match_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("match_runs.id"))
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id"))
    score: Mapped[float] = mapped_column(Float, nullable=False)
    matched_skills: Mapped[List[str]] = mapped_column(JSON, default=list)
    missing_skills: Mapped[List[str]] = mapped_column(JSON, default=list)
    highlights: Mapped[List[str]] = mapped_column(JSON, default=list)
    rationale: Mapped[str] = mapped_column(Text, default="")

    run: Mapped[MatchRun] = relationship("MatchRun", back_populates="results")
    candidate: Mapped[CandidateProfile] = relationship("CandidateProfile", back_populates="match_results")
