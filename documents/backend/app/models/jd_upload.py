from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class JDUpload(Base):
    __tablename__ = "jd_uploads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
