from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ResumeUploadItem(BaseModel):
    id: int
    original_filename: str
    status: str
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class UploadResumesResponse(BaseModel):
    uploads: List[ResumeUploadItem]


class UploadStatusResponse(BaseModel):
    id: int
    status: str
    error_message: Optional[str] = None
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MatchCandidateSummary(BaseModel):
    candidate_id: int
    full_name: Optional[str]
    email: Optional[str] = None
    phone: Optional[str] = None
    score: float
    matched_skills: List[str]
    missing_skills: List[str]
    highlights: List[str]
    rationale: str
    ai_summary: Optional[str] = None

    class Config:
        from_attributes = True


class MatchRunRequest(BaseModel):
    job_title: str = Field(..., example="Senior Backend Engineer")
    job_description: Optional[str] = Field(None, example="We are looking for...")
    must_have_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    candidate_ids: Optional[List[int]] = Field(
        default=None,
        description="Optional subset of candidate profile IDs to match against",
    )
    jd_id: Optional[int] = Field(
        default=None,
        description="Optional JD upload id; if provided, text is pulled from stored JD",
    )


class MatchRunResponse(BaseModel):
    run_id: int
    results: List[MatchCandidateSummary]
    total_candidates: int


class CandidateProfileResponse(BaseModel):
    id: int
    full_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    summary: Optional[str]
    skills: List[str]
    experiences: List[Any]
    education: List[Any]
    raw_text: str
    uploaded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CandidateChatMessage(BaseModel):
    role: str
    content: str


class CandidateChatRequest(BaseModel):
    message: str
    history: List[CandidateChatMessage] = Field(default_factory=list)
    job_description: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)


class CandidateChatResponse(BaseModel):
    reply: str
    supporting_points: List[str] = Field(default_factory=list)


class DownloadZipRequest(BaseModel):
    candidate_ids: List[int] = Field(..., description="Candidate profile IDs to include in the ZIP")


class UploadJDResponse(BaseModel):
    jd_id: int
    title: Optional[str]
    original_filename: str
    extracted_text: str
    uploaded_at: datetime

    class Config:
        from_attributes = True
