"""
Database models initialization
"""

from app.models.user import User
from app.models.matcher import (
    Job,
    ResumeUpload,
    CandidateProfile,
    MatchRun,
    MatchResult,
)
from app.models.jd_upload import JDUpload
from app.models.document import DocumentTemplate, GeneratedDocument, DocumentConversation
from app.models.interview import Interview

__all__ = ["User", "Job", "ResumeUpload", "CandidateProfile", "MatchRun", "MatchResult", "JDUpload", "DocumentTemplate", "GeneratedDocument", "Interview", "DocumentConversation"]
