from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TranscriptItem(BaseModel):
  id: str
  question: str
  answer: Optional[str] = None


class AIDetectionResult(BaseModel):
  """AI-generated resume detection result."""
  is_ai_generated: bool
  confidence_score: float = Field(ge=0, le=100)
  risk_level: str = Field(pattern="^(high|medium|low)$")
  indicators: List[Dict[str, Any]] = []
  explanation: str
  detailed_analysis: Dict[str, float] = {}


class InterviewBase(BaseModel):
  candidate_name: str
  candidate_email: Optional[str] = None
  role: str
  company: Optional[str] = "Your Company"
  round_type: str
  scheduled_at: datetime
  notes: Optional[str] = None
  resume_filename: Optional[str] = None
  jd_filename: Optional[str] = None
  jd_text: Optional[str] = None


class InterviewCreate(InterviewBase):
  pass


class InterviewUpdateStatus(BaseModel):
  status: str = Field(..., pattern="^(scheduled|ongoing|completed|cancelled)$")


class QuestionCreate(BaseModel):
  question: str


class ResponseCreate(BaseModel):
  question_id: str
  answer: str


class FeedbackCreate(BaseModel):
  rating: int = Field(ge=1, le=5)
  decision: str
  comments: Optional[str] = None
  notes: Optional[str] = None


class InterviewOut(BaseModel):
  id: int
  candidate_name: str
  candidate_email: Optional[str]
  role: str
  company: Optional[str]
  round_type: str
  scheduled_at: datetime
  status: str
  interviewer_key: str
  candidate_key: str
  notes: Optional[str]
  resume_filename: Optional[str]
  jd_filename: Optional[str]
  jd_text: Optional[str]
  transcript: List[TranscriptItem] = []
  feedback: Optional[dict] = None
  ai_detection: Optional[AIDetectionResult] = None

  class Config:
    orm_mode = True


class ResolveOut(BaseModel):
  role: str
  interview: InterviewOut
