"""
Document Management API Endpoints
Handles HR letter templates, generation, and retrieval
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List
import csv
import io
import hashlib
from datetime import datetime

from app.db.session import get_db
from app.core.auth import get_current_active_user
from app.models.user import User
from app.models.document import DocumentTemplate, GeneratedDocument
from app.schemas.document import (
    DocumentTemplateResponse,
    AgentMessageResponse,
    TemplateSelectionRequest,
    InputMethodRequest,
    ManualFieldInput,
    ManualEntryComplete,
    CSVUploadRequest,
    DocumentQueryResponse,
    GeneratedDocumentResponse,
    GeneratedDocumentDetail,
    DocumentEmailRequest,
    DocumentPreviewRequest,
    DocumentGenerateRequest,
    PreviewResponse,
    DocumentChatRequest,
    DocumentChatResponse
)
from app.services.document_agent import DocumentAgentService
from app.services.document_chat import DocumentChatService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/templates", response_model=List[DocumentTemplateResponse])
async def list_templates(
    category: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List available document templates
    HR users only
    """
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR users can access document templates"
        )
    
    query = select(DocumentTemplate).where(DocumentTemplate.is_active.is_(True))
    if category:
        query = query.where(DocumentTemplate.category == category)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return templates


@router.get("/templates/{template_id}/csv-template")
async def download_csv_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download CSV template with column headers for a specific template"""
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    result = await db.execute(
        select(DocumentTemplate).where(DocumentTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Determine fields: prefer PDF-extracted placeholders if available
    agent_tmp = DocumentAgentService(db)
    pdf_required, pdf_optional = agent_tmp._extract_fields_from_pdf(template.name)
    required_fields = pdf_required or template.required_fields
    optional_fields = pdf_optional or template.optional_fields

    # Generate CSV with headers
    output = io.StringIO()
    writer = csv.DictWriter(
        output, 
        fieldnames=(required_fields or []) + (optional_fields or [])
    )
    writer.writeheader()
    
    # Add sample row with realistic examples per field
    def example_for(field: str) -> str:
        f = field.lower()
        examples = {
            "employee_name": "John Michael Doe",
            "candidate_name": "Jane Smith",
            "designation": "Senior Software Engineer",
            "current_designation": "Software Engineer",
            "new_designation": "Senior Software Engineer",
            "department": "Engineering",
            "new_department": "Platform",
            "joining_date": "01/12/2024",
            "offer_acceptance_date": "30/11/2024",
            "confirmation_date": "15/06/2024",
            "last_working_date": "31/10/2024",
            "effective_date": "01/01/2025",
            "salary": "85000",
            "new_salary": "95000",
            "increment_amount": "10000",
            "location": "Chennai",
            "current_location": "Bengaluru",
            "new_location": "Chennai",
            "transfer_date": "15/01/2025",
            "reporting_manager": "Alice Johnson",
            "phone_number": "+91-80-12345678",
            "email": "john.doe@example.com",
            "company_name": "DHL IT SERVICES",
            "company_address": "CHENNAI ONE IT SEZ",
            "contact_info": "+91-80-12345678 | hr@company.com",
            "reason": "Business requirements",
            "reason_for_termination": "Policy violation",
            "termination_date": "15/12/2024",
            "probation_period": "6 months",
            "probation_feedback": "Meets expectations",
            "employee_code": "EMP-1024",
            "skills": "Python; React; SQL",
            "achievements": "Top Performer 2024",
            "responsibilities": "Backend development; API design",
            "issue_date": "27/11/2025",
            "warning_type": "Performance Warning",
            "signatory_name": "Robert Williams",
            "signatory_designation": "HR Manager",
        }
        return examples.get(f, f"<{field}>")

    sample_row = {field: example_for(field) for field in (required_fields or []) + (optional_fields or [])}
    writer.writerow(sample_row)
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={template.name.replace(' ', '_')}_template.csv"
        }
    )


@router.post("/chat", response_model=DocumentChatResponse)
async def document_chat(
    request: DocumentChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    AI-powered conversational document generation
    Natural language interface for creating HR documents
    """
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    try:
        chat_service = DocumentChatService()
        response = chat_service.generate_response(
            user_message=request.message,
            conversation_history=request.conversation_history,
            available_templates=request.available_templates,
            session_context={"session_id": request.session_id}
        )
        return DocumentChatResponse(**response)
    except Exception as e:
        print(f"Chat service error: {e}")
        # Fallback response
        template_names = [t.get('name', '') for t in request.available_templates]
        return DocumentChatResponse(
            reply=f"I can help you create: {', '.join(template_names)}. Which document do you need?",
            action=None,
            is_complete=False
        )


@router.post("/agent/start", response_model=AgentMessageResponse)
async def start_agent_conversation(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Start a new conversation with the document agent"""
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    agent = DocumentAgentService(db)
    response = await agent.start_conversation(current_user.id)
    
    return AgentMessageResponse(**response)


@router.post("/agent/select-template", response_model=AgentMessageResponse)
async def select_template(
    request: TemplateSelectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Select a template in the conversation"""
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    agent = DocumentAgentService(db)
    response = await agent.process_template_selection(
        request.session_id,
        request.template_id
    )
    
    return AgentMessageResponse(**response)


@router.post("/agent/input-method", response_model=AgentMessageResponse)
async def choose_input_method(
    request: InputMethodRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Choose how to provide data (manual entry, upload CSV or download template)"""
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    agent = DocumentAgentService(db)
    response = await agent.process_input_method(
        request.session_id,
        request.method
    )
    
    return AgentMessageResponse(**response)


@router.post("/agent/manual-field", response_model=AgentMessageResponse)
async def submit_manual_field(
    request: ManualFieldInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Submit a single field value in manual entry mode"""
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    agent = DocumentAgentService(db)
    response = await agent.process_manual_field(
        request.session_id,
        request.field_name,
        request.field_value
    )
    
    return AgentMessageResponse(**response)


@router.post("/agent/manual-complete", response_model=AgentMessageResponse)
async def complete_manual_entry(
    request: ManualEntryComplete,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Complete manual entry - add another or generate documents"""
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    agent = DocumentAgentService(db)
    response = await agent.process_manual_complete(
        request.session_id,
        request.action,
        current_user.id
    )
    
    return AgentMessageResponse(**response)


@router.post("/agent/preview", response_model=PreviewResponse)
async def preview_document(
    request: DocumentPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Preview document before generation with validation"""
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    try:
        agent = DocumentAgentService(db)
        response = await agent.generate_preview(request.session_id)
        
        # Ensure preview_html is a string
        if response.get("preview_html") is None:
            response["preview_html"] = ""
        
        return PreviewResponse(**response)
    except Exception as e:
        print(f"❌ Error in preview_document: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/generate", response_model=AgentMessageResponse)
async def generate_document(
    request: DocumentGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate final document in PDF or DOCX format"""
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    try:
        agent = DocumentAgentService(db)
        response = await agent.generate_documents(
            request.session_id,
            current_user.id,
            request.format
        )
        
        return AgentMessageResponse(**response)
    except Exception as e:
        print(f"❌ Error in generate_document: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/upload-csv", response_model=AgentMessageResponse)
async def upload_csv_data(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload CSV file and generate documents"""
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    # Parse CSV file
    content = await file.read()
    csv_text = content.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(csv_text))
    csv_data = list(csv_reader)
    
    if not csv_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is empty"
        )
    
    agent = DocumentAgentService(db)
    response = await agent.process_csv_upload(
        session_id,
        csv_data,
        current_user.id
    )
    
    return AgentMessageResponse(**response)


@router.post("/agent/upload-signature", response_model=AgentMessageResponse)
async def upload_signature(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload e-signature image"""
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PNG, JPG, and JPEG files are allowed for signatures"
        )
    
    # Read and store signature
    signature_data = await file.read()
    
    agent = DocumentAgentService(db)
    response = await agent.process_signature_upload(
        session_id,
        signature_data,
        file.filename
    )
    
    return AgentMessageResponse(**response)


@router.get("/query", response_model=DocumentQueryResponse)
async def query_documents(
    employee_code: str = None,
    phone_number: str = None,
    document_type: str = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Search and retrieve previously generated documents
    Can search by employee_code, phone_number, or document_type
    """
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    filters = []
    
    if employee_code:
        filters.append(GeneratedDocument.employee_code == employee_code)
    
    if phone_number:
        phone_hash = hashlib.sha256(phone_number.encode()).hexdigest()
        filters.append(GeneratedDocument.phone_number_hash == phone_hash)
    
    if document_type:
        filters.append(GeneratedDocument.document_type == document_type)
    
    query = select(GeneratedDocument)
    if filters:
        query = query.where(or_(*filters))
    
    query = query.order_by(GeneratedDocument.generated_at.desc()).limit(limit)
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    # Prefer masked preview in response
    docs_resp = []
    for doc in documents:
        payload = GeneratedDocumentResponse.from_orm(doc)
        data = payload.dict()
        data["preview_masked_html"] = getattr(doc, "preview_masked_html", None)
        docs_resp.append(GeneratedDocumentResponse(**data))
    return DocumentQueryResponse(
        documents=docs_resp,
        total=len(documents)
    )


@router.get("/{document_id}", response_model=GeneratedDocumentDetail)
async def get_document_details(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get document details with decrypted metadata"""
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    result = await db.execute(
        select(GeneratedDocument).where(GeneratedDocument.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Decrypt name for display
    agent = DocumentAgentService(db)
    decrypted_name = agent._decrypt_data(document.recipient_name_encrypted)
    
    return GeneratedDocumentDetail(
        **GeneratedDocumentResponse.from_orm(document).dict(),
        recipient_name=decrypted_name,
        file_url=f"/api/v1/documents/{document_id}/download"
    )


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    format: str = "pdf",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download generated document as PDF or DOCX"""
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    result = await db.execute(
        select(GeneratedDocument).where(GeneratedDocument.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Build meaningful filename: name_lettertype_date
    agent = DocumentAgentService(db)
    recipient_name = agent._decrypt_data(document.recipient_name_encrypted)
    safe_name = (recipient_name or "document").replace(" ", "_")
    safe_type = (document.document_type or "letter").replace(" ", "_")
    today = datetime.now().strftime("%Y-%m-%d")
    
    if format.lower() == "pdf":
        # Generate professional PDF using DocumentGenerator
        from app.utils.document_generator import DocumentGenerator
        
        pdf_buffer = io.BytesIO()
        
        # Prepare document data for generation
        document_data = document.document_data or {}
        document_data['content'] = document.content or ""
        document_data['company_name'] = "DHL Group"
        document_data['company_address'] = "Corporate Headquarters\nBonn, Germany"
        document_data['contact_info'] = "hr@dhl.com | +49 228 182 0"
        
        # Generate PDF with proper formatting
        DocumentGenerator.generate_pdf_from_template(
            template_path=None,  # Using content directly
            data=document_data,
            output_stream=pdf_buffer
        )
        
        pdf_buffer.seek(0)
        filename = f"{safe_name}_{safe_type}_{today}.pdf"
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    elif format.lower() == "docx":
        # Generate DOCX using DocumentGenerator
        from app.utils.document_generator import DocumentGenerator
        
        docx_buffer = io.BytesIO()
        
        # Prepare document data for generation
        document_data = document.document_data or {}
        document_data['content'] = document.content or ""
        document_data['company_name'] = "DHL Group"
        document_data['company_address'] = "Corporate Headquarters\nBonn, Germany"
        document_data['contact_info'] = "hr@dhl.com | +49 228 182 0"
        
        # Generate DOCX with proper formatting
        DocumentGenerator.generate_docx_from_template(
            template_path=None,  # Using content directly
            data=document_data,
            output_stream=docx_buffer
        )
        
        docx_buffer.seek(0)
        filename = f"{safe_name}_{safe_type}_{today}.docx"
        return StreamingResponse(
            docx_buffer,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    else:
        # Fallback plain text download
        filename = f"{safe_name}_{safe_type}_{today}.txt"
        return StreamingResponse(
            io.BytesIO((document.content or "").encode()),
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )


@router.post("/download-bulk")
async def download_bulk_documents(
    document_ids: List[int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download multiple documents as ZIP file"""
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    import zipfile
    
    # Fetch all documents
    result = await db.execute(
        select(GeneratedDocument).where(GeneratedDocument.id.in_(document_ids))
    )
    documents = result.scalars().all()
    
    if not documents:
        raise HTTPException(status_code=404, detail="No documents found")
    
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for doc in documents:
            filename = f"{doc.document_type}_{doc.id}.txt"
            zip_file.writestr(filename, doc.content)
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=documents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        }
    )


@router.post("/{document_id}/send-email")
async def send_document_email(
    document_id: int,
    email_request: DocumentEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Send document via email"""
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    result = await db.execute(
        select(GeneratedDocument).where(GeneratedDocument.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Generate PDF attachment
        from app.utils.document_generator import DocumentGenerator
        
        pdf_buffer = io.BytesIO()
        document_data = document.document_data or {}
        document_data['content'] = document.content or ""
        document_data['company_name'] = "DHL Group"
        document_data['company_address'] = "Corporate Headquarters\nBonn, Germany"
        document_data['contact_info'] = "hr@dhl.com | +49 228 182 0"
        
        # Generate PDF for email attachment
        DocumentGenerator.generate_pdf_from_template(
            template_path=None,
            data=document_data,
            output_stream=pdf_buffer
        )
        
        # Get document details for filename
        agent = DocumentAgentService(db)
        recipient_name = agent._decrypt_data(document.recipient_name_encrypted)
        safe_name = (recipient_name or "document").replace(" ", "_")
        safe_type = (document.document_type or "letter").replace(" ", "_")
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"{safe_name}_{safe_type}_{today}.pdf"
        
        # Send email with attachment
        from app.utils.email_service import EmailService
        email_service = EmailService()
        
        success = await email_service.send_document_email(
            recipient_email=email_request.recipient_email,
            cc_emails=email_request.cc_emails,
            subject=f"Document: {safe_type.replace('_', ' ').title()}",
            document_content=document.content or "",
            pdf_attachment=pdf_buffer.getvalue(),
            attachment_filename=filename,
            sender_name=current_user.full_name
        )
        
        if success:
            # Update document status
            document.email_sent = True
            document.status = "sent"
            await db.commit()
            
            return {
                "message": "Email sent successfully",
                "recipient": email_request.recipient_email
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail="Failed to send email"
            )
            
    except Exception as e:
        print(f"Email sending error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to send email"
        )


@router.post("/{document_id}/sign")
async def add_digital_signature(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add digital signature to document"""
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    result = await db.execute(
        select(GeneratedDocument).where(GeneratedDocument.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # In production, implement digital signature
    document.digitally_signed = True
    document.status = "signed"
    await db.commit()
    
    return {
        "message": "Document signed successfully",
        "signed_by": current_user.full_name
    }

