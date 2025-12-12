"""
Import all models so Base.metadata has them before create_all.
"""
from app.db.session import Base
from app.models.user import User
from app.models.matcher import Job, ResumeUpload, CandidateProfile, MatchRun, MatchResult
from app.models.jd_upload import JDUpload
from app.models.interview import Interview
from app.models.document import DocumentTemplate, GeneratedDocument, DocumentConversation

__all__ = [
    "Base",
    "User",
    "Job",
    "ResumeUpload",
    "CandidateProfile",
    "MatchRun",
    "MatchResult",
    "JDUpload",
    "Interview",
    "DocumentTemplate",
    "GeneratedDocument",
    "DocumentConversation",
]
