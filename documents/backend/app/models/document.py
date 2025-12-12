from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class DocumentTemplate(Base):
    """HR Letter Templates"""
    __tablename__ = "document_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)  # e.g., "Offer Letter", "Experience Letter"
    category = Column(String, index=True)  # e.g., "recruitment", "employment", "exit"
    file_path = Column(String)  # Path to .docx template
    description = Column(Text)
    
    # CSV column metadata for this template
    required_fields = Column(JSON)  # ["employee_name", "designation", "salary", ...]
    optional_fields = Column(JSON)  # ["middle_name", "department", ...]
    
    # Branding
    uses_company_logo = Column(Boolean, default=True)
    uses_company_letterhead = Column(Boolean, default=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    generated_documents = relationship("GeneratedDocument", back_populates="template")


class GeneratedDocument(Base):
    """Generated HR letters (encrypted metadata only)"""
    __tablename__ = "generated_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("document_templates.id"))
    
    # Storage identifiers (encrypted)
    employee_code = Column(String, index=True, nullable=True)  # For existing employees
    phone_number_hash = Column(String, index=True, nullable=True)  # Hashed phone for freshers
    email_hash = Column(String, index=True, nullable=True)  # Hashed email for search fallback
    
    # Metadata (encrypted)
    recipient_name_encrypted = Column(Text)  # Encrypted name
    document_type = Column(String, index=True)  # "offer_letter", "experience_letter", etc.
    
    # Document content
    content = Column(Text, nullable=True)  # Generated document content
    document_data = Column(JSON, nullable=True)  # Field data used to generate document
    preview_masked_html = Column(Text, nullable=True)  # Privacy-safe preview for UI
    
    # File reference
    file_storage_path = Column(String, nullable=True)  # Encrypted file path or S3 key
    file_hash = Column(String, nullable=True)  # SHA-256 hash for integrity
    
    # Audit trail
    generated_by = Column(Integer, ForeignKey("users.id"))
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    # Status
    status = Column(String, default="draft")  # draft, sent, signed, archived
    email_sent = Column(Boolean, default=False)
    digitally_signed = Column(Boolean, default=False)
    
    # Job/Candidate linking
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    
    # Relationships
    template = relationship("DocumentTemplate", back_populates="generated_documents")
    generated_by_user = relationship("User")
    job = relationship("Job")


class DocumentConversation(Base):
    """Agentic bot conversation state for document generation"""
    __tablename__ = "document_conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Conversation state
    current_step = Column(String, default="initial")  # initial, template_selection, input_method, csv_upload, preview, complete
    selected_template_id = Column(Integer, ForeignKey("document_templates.id"), nullable=True)
    input_method = Column(String, nullable=True)  # "upload_csv", "download_template"
    
    # Conversation context (JSON)
    context = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User")
    template = relationship("DocumentTemplate")
