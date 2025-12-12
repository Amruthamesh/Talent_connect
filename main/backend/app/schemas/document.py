from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


# Template Schemas
class DocumentTemplateBase(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    required_fields: List[str] = []
    optional_fields: List[str] = []
    uses_company_logo: bool = True
    uses_company_letterhead: bool = True


class DocumentTemplateCreate(DocumentTemplateBase):
    file_path: str


class DocumentTemplateResponse(DocumentTemplateBase):
    id: int
    file_path: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Generated Document Schemas
class GeneratedDocumentBase(BaseModel):
    template_id: int
    document_type: str
    job_id: Optional[int] = None


class GeneratedDocumentCreate(GeneratedDocumentBase):
    employee_code: Optional[str] = None
    phone_number: Optional[str] = None
    recipient_data: Dict[str, Any]  # Actual data to fill template


class GeneratedDocumentResponse(BaseModel):
    id: int
    template_id: int
    document_type: str
    generated_at: datetime
    status: str
    email_sent: bool
    digitally_signed: bool
    
    class Config:
        from_attributes = True


class GeneratedDocumentDetail(GeneratedDocumentResponse):
    recipient_name: str  # Decrypted for display
    file_url: Optional[str] = None  # Temporary signed URL


# Agent Conversation Schemas
class AgentMessageRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class AgentMessageResponse(BaseModel):
    session_id: str
    message: str
    current_step: str
    options: Optional[List[Dict[str, Any]]] = None
    templates: Optional[List[Dict[str, Any]]] = None
    next_step: Optional[str] = None
    requires_upload: bool = False
    csv_download_url: Optional[str] = None
    required_fields: Optional[List[str]] = None
    optional_fields: Optional[List[str]] = None
    current_field: Optional[str] = None
    generated_count: Optional[int] = None
    document_ids: Optional[List[int]] = None
    preview_data: Optional[List[Dict[str, Any]]] = None
    template_name: Optional[str] = None


class TemplateSelectionRequest(BaseModel):
    session_id: str
    template_id: int


class InputMethodRequest(BaseModel):
    session_id: str
    method: str  # "manual_entry", "upload_csv" or "download_template"


class ManualFieldInput(BaseModel):
    session_id: str
    field_name: str
    field_value: str


class ManualEntryComplete(BaseModel):
    session_id: str
    action: str  # "add_another" or "generate"


class CSVUploadRequest(BaseModel):
    session_id: str
    csv_data: List[Dict[str, Any]]


class DocumentPreviewRequest(BaseModel):
    session_id: str


class DocumentGenerateRequest(BaseModel):
    session_id: str
    format: str = "pdf"  # pdf or docx


class PreviewResponse(BaseModel):
    session_id: str
    preview_html: str
    validation_errors: Optional[Dict[str, str]] = None
    all_fields_valid: bool
    collected_data: Dict[str, Any]


class DocumentDownloadRequest(BaseModel):
    document_id: int
    format: str = "pdf"  # pdf or docx


class DocumentEmailRequest(BaseModel):
    document_id: int
    recipient_email: str
    cc_emails: Optional[List[str]] = []
    subject: Optional[str] = None
    body: Optional[str] = None


class DocumentQueryRequest(BaseModel):
    employee_code: Optional[str] = None
    phone_number: Optional[str] = None
    document_type: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = 20


class DocumentQueryResponse(BaseModel):
    documents: List[GeneratedDocumentResponse]


# Document Chat Schemas
class DocumentChatRequest(BaseModel):
    message: str
    session_id: str
    conversation_history: List[Dict[str, str]]
    available_templates: List[Dict[str, Any]]


class DocumentChatResponse(BaseModel):
    reply: str
    action: Optional[str] = None
    action_data: Optional[Dict[str, Any]] = None
    is_complete: bool = False
