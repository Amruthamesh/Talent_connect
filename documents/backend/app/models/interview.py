from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from app.db.session import Base


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    candidate_name = Column(String(255), nullable=False)
    candidate_email = Column(String(255), nullable=True)
    role = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    round_type = Column(String(100), nullable=False, default="Behavioral")
    scheduled_at = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False, default="scheduled")
    interviewer_key = Column(String(255), nullable=False, unique=True, index=True)
    candidate_key = Column(String(255), nullable=False, unique=True, index=True)
    notes = Column(Text, nullable=True)
    resume_filename = Column(String(255), nullable=True)
    jd_filename = Column(String(255), nullable=True)
    jd_text = Column(Text, nullable=True)
    transcript = Column(JSON, nullable=False, default=list)
    feedback_rating = Column(Integer, nullable=True)
    feedback_decision = Column(String(100), nullable=True)
    feedback_comments = Column(Text, nullable=True)
    feedback_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "candidate_name": self.candidate_name,
            "candidate_email": self.candidate_email,
            "role": self.role,
            "company": self.company,
            "round_type": self.round_type,
            "scheduled_at": self.scheduled_at,
            "status": self.status,
            "interviewer_key": self.interviewer_key,
            "candidate_key": self.candidate_key,
            "notes": self.notes,
            "resume_filename": self.resume_filename,
            "jd_filename": self.jd_filename,
            "jd_text": self.jd_text,
            "transcript": self.transcript or [],
            "feedback": {
                "rating": self.feedback_rating,
                "decision": self.feedback_decision,
                "comments": self.feedback_comments,
                "notes": self.feedback_notes,
            } if self.feedback_rating or self.feedback_decision or self.feedback_comments or self.feedback_notes else None,
        }
