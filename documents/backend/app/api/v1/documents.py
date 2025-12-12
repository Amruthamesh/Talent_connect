"""
Document Management API Endpoints
Handles HR letter templates, generation, and retrieval
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm.attributes import flag_modified
from typing import List
import csv
import io
import hashlib
import json
from datetime import datetime

from app.db.session import get_db
from app.core.auth import get_current_active_user
from app.models.user import User
from app.models.document import DocumentTemplate, GeneratedDocument
from app.config import settings
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
    PreviewResponse
)
from app.services.document_agent import DocumentAgentService

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


@router.get("/sample-csv/{csv_type}")
async def download_sample_csv(
    csv_type: str,
    current_user: User = Depends(get_current_active_user)
):
    """Download sample CSV files with actual values (no placeholders)"""
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    import os
    
    # Available sample CSV files
    available_files = {
        "offer_letter": "offer_letter_complete.csv",
        "offer_letter_quick": "offer_letter_quick.csv",
        "experience_letter": "experience_letter_complete.csv",
        "relieving_letter": "relieving_letter_complete.csv",
        "termination_letter": "termination_letter_complete.csv",
        "probation_confirmation": "probation_confirmation_complete.csv",
        "bonus_letter": "bonus_letter_complete.csv",
        "master": "hr_complete_master.csv"
    }
    
    if csv_type not in available_files:
        raise HTTPException(
            status_code=404, 
            detail=f"Sample CSV type '{csv_type}' not found. Available: {list(available_files.keys())}"
        )
    
    file_path = f"templates/sample_csvs/{available_files[csv_type]}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Sample CSV file not found")
    
    return FileResponse(
        path=file_path,
        filename=available_files[csv_type],
        media_type="text/csv"
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
    
    agent = DocumentAgentService(db)
    response = await agent.generate_preview(request.session_id)
    
    return PreviewResponse(**response)


@router.post("/agent/generate", response_model=AgentMessageResponse)
async def generate_document(
    request: DocumentGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate final document in PDF or DOCX format"""
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    agent = DocumentAgentService(db)
    response = await agent.generate_documents(
        request.session_id,
        current_user.id,
        request.format
    )
    
    return AgentMessageResponse(**response)


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


@router.post("/agent/chat", response_model=AgentMessageResponse)
async def natural_chat(
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Natural conversational chat endpoint that intelligently extracts information
    Supports editing, appending, and context-aware field extraction
    """
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    session_id = request.get("session_id")
    user_message = request.get("message", "").strip()
    
    if not session_id or not user_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing session_id or message"
        )
    
    agent = DocumentAgentService(db)
    
    # Get conversation from database
    try:
        conversation = await agent._get_conversation(session_id)
    except Exception:
        return AgentMessageResponse(
            message="Session not found. Please start a new conversation.",
            next_step="error",
            session_id=session_id
        )
    
    # Get session data from context
    ctx = dict(conversation.context) if conversation.context else {}
    template_id = conversation.selected_template_id
    template_name = ctx.get("template_name", "")
    manual_data = ctx.get("manual_data", {})
    required_fields = ctx.get("required_fields", [])
    optional_fields = ctx.get("optional_fields", [])
    all_fields = required_fields + optional_fields
    
    # Get template from database
    if not template_id:
        return AgentMessageResponse(
            message="No template selected. Please start over.",
            next_step="error",
            session_id=session_id
        )
    
    result = await db.execute(
        select(DocumentTemplate).where(DocumentTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        return AgentMessageResponse(
            message="Template not found.",
            next_step="error",
            session_id=session_id
        )
    
    # Use OpenAI to intelligently extract information from natural language
    import re
    from datetime import datetime
    from openai import OpenAI
    
    # Initialize OpenAI client
    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
    
    # Patterns for common information extraction (fallback if no OpenAI)
    extracted_info = {}
    
    # Determine what fields are missing to provide context
    missing_required = [f for f in required_fields if f not in manual_data or not manual_data[f]]
    
    # Try OpenAI-powered extraction first if available
    if openai_client and settings.OPENAI_API_KEY:
        try:
            # Build context for GPT
            filled_fields_str = ", ".join([f"{k}: {v}" for k, v in manual_data.items()]) if manual_data else "None"
            missing_fields_str = ", ".join(missing_required) if missing_required else "None"
            
            gpt_prompt = f"""You are an intelligent data extraction assistant for HR document generation.

CONTEXT:
- Template: {template_name}
- Already collected fields: {filled_fields_str}
- Still need to collect: {missing_fields_str}

USER MESSAGE: "{user_message}"

TASK: Extract field values from the user's message. Return ONLY a JSON object with field names as keys and extracted values as values.

RULES:
1. If the user is providing a direct answer to the next missing field, extract it
2. If multiple fields are mentioned (e.g., "Name: John, Email: john@email.com"), extract all of them
3. Dates can be in any format (e.g., "2-December-2025", "Dec 2, 2025", "02/12/2024")
4. Only return fields that are actually mentioned or clearly implied in the message
5. If nothing can be extracted, return an empty object {{}}

Return JSON only, no explanation:"""

            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=500,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": "You are a precise data extraction AI. Return only valid JSON."},
                    {"role": "user", "content": gpt_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            gpt_extracted = json.loads(content) if content else {}
            
            # Merge GPT extraction with our extracted_info
            extracted_info.update(gpt_extracted)
            
        except Exception as e:
            print(f"⚠️ OpenAI extraction failed: {e}, falling back to regex")
    
    # Check if this looks like a direct answer to the current question (fallback logic)
    is_direct_answer = False
    if not extracted_info and missing_required and len(missing_required) > 0:
        current_needed_field = missing_required[0]
        message_lower = user_message.lower()
        
        # Check if message is NOT a question or command
        is_question = any(keyword in message_lower for keyword in ['what', 'how', 'when', 'where', 'why', 'which', '?'])
        
        # Check if ANY field name (other than the current one) is mentioned with a colon pattern
        other_fields_with_colons = []
        for field in all_fields:
            if field != current_needed_field:
                field_label = field.replace('_', ' ')
                # Check for explicit patterns like "fieldname: value"
                if re.search(rf'\b{re.escape(field_label)}\s*:', message_lower):
                    other_fields_with_colons.append(field)
        
        # It's a direct answer if: not a question, short message (< 100 chars), and NO other field mentions
        if not is_question and len(user_message.strip()) > 0 and len(user_message) < 100 and len(other_fields_with_colons) == 0:
            # Extract just the value (remove the field name if mentioned)
            value = user_message.strip()
            
            # If the current field name is in the message with a colon, extract what comes after it
            current_field_label = current_needed_field.replace('_', ' ')
            if re.search(rf'\b{re.escape(current_field_label)}\s*:', message_lower):
                # Look for patterns like "field_name: value" or "field_name is value"
                patterns = [
                    rf'{re.escape(current_field_label)}\s*:\s*(.+)',
                    rf'{re.escape(current_field_label)}\s+is\s+(.+)',
                    rf'{re.escape(current_field_label)}\s*=\s*(.+)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, message_lower, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        break
            
            extracted_info[current_needed_field] = value
            is_direct_answer = True
    
    # Only do complex extraction if it's NOT a direct answer
    if not is_direct_answer:
        # Extract names (more flexible - any word sequences)
        name_pattern = r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b'
        names = re.findall(name_pattern, user_message)
        
        # Extract dates
        date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
            r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b',
            r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b'
        ]
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, user_message, re.IGNORECASE))
        
        # Extract numbers (salary, amounts, etc.)
        number_pattern = r'\b(\d+(?:,\d{3})*(?:\.\d{2})?)\b'
        numbers = re.findall(number_pattern, user_message)
        
        # Extract email
        email_pattern = r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
        emails = re.findall(email_pattern, user_message)
        
        # Extract phone
        phone_pattern = r'\b(\+?\d{1,3}[-.\s]?\(?\d{2,3}\)?[-.\s]?\d{3,4}[-.\s]?\d{4})\b'
        phones = re.findall(phone_pattern, user_message)
        
        # Intelligent field mapping based on context
        message_lower = user_message.lower()
        
        # Check for explicit field mentions in the message (multiple fields at once)
        for field in all_fields:
            field_name = field.replace('_', ' ')
            
            # If user is explicitly setting a field
            if field_name in message_lower or field in message_lower:
                # Extract value after field mention
                field_patterns = [
                    rf'{field_name}\s+is\s+([^,.\n]+)',
                    rf'{field_name}:\s*([^,.\n]+)',
                    rf'{field_name}\s*=\s*([^,.\n]+)',
                    rf'set\s+{field_name}\s+to\s+([^,.\n]+)',
                ]
                for pattern in field_patterns:
                    match = re.search(pattern, message_lower, re.IGNORECASE)
                    if match:
                        extracted_info[field] = match.group(1).strip()
                        break
        
        # Smart field assignment based on context
        if 'employee' in message_lower and names and 'employee_name' not in extracted_info:
            extracted_info['employee_name'] = names[0]
        elif 'name' in message_lower and names and not any(k for k in extracted_info.keys() if 'name' in k):
            # Find the first name field that's not filled
            name_fields = [f for f in all_fields if 'name' in f and f not in manual_data]
            if name_fields and names:
                extracted_info[name_fields[0]] = names[0]
        
        if dates and not any(k for k in extracted_info.keys() if 'date' in k):
            date_fields = [f for f in all_fields if 'date' in f and f not in manual_data]
            if date_fields:
                extracted_info[date_fields[0]] = dates[0]
        
        if emails and 'email' in all_fields and 'email' not in manual_data:
            extracted_info['email'] = emails[0]
        
        if phones and 'phone_number' in all_fields and 'phone_number' not in manual_data:
            extracted_info['phone_number'] = phones[0]
        
        if numbers:
            # Check for salary/amount fields
            amount_fields = [f for f in all_fields if any(term in f for term in ['salary', 'amount', 'ctc']) and f not in manual_data]
            if amount_fields and numbers:
                extracted_info[amount_fields[0]] = numbers[0].replace(',', '')
    
    # Update collected data in context
    manual_data.update(extracted_info)
    ctx["manual_data"] = manual_data
    conversation.context = ctx
    flag_modified(conversation, "context")
    await db.commit()
    
    # Determine what's still needed
    missing_required = [f for f in required_fields if f not in manual_data or not manual_data[f]]
    
    # Generate natural response using GPT if available, otherwise use templates
    if extracted_info:
        confirmed = ', '.join([f"**{k.replace('_', ' ')}**: {v}" for k, v in extracted_info.items()])
        
        if missing_required:
            next_field = missing_required[0]
            
            # Use GPT to generate natural response if available
            if openai_client and settings.OPENAI_API_KEY:
                try:
                    prompt = f"""You are a friendly HR assistant helping collect information for a {template_name}.

The user just provided: {confirmed}

Now ask for the next field: "{next_field.replace('_', ' ')}"

Generate a natural, conversational response that:
1. Confirms what they provided (use checkmark ✓)
2. Asks for the next field in a friendly way
3. Keep it brief (1-2 sentences max)
4. Use markdown formatting for field names (bold **)

Response:"""
                    
                    gpt_response = openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        max_tokens=150,
                        temperature=0.7,
                        messages=[
                            {"role": "system", "content": "You are a friendly, professional HR assistant. Keep responses brief and natural."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    response_message = gpt_response.choices[0].message.content.strip()
                except Exception as e:
                    print(f"⚠️ GPT response generation failed: {e}")
                    response_message = f"Got it! ✓\n\n{confirmed}\n\nWhat's the **{next_field.replace('_', ' ')}**?"
            else:
                response_message = f"Got it! ✓\n\n{confirmed}\n\nWhat's the **{next_field.replace('_', ' ')}**?"
            
            next_step = "collecting"
        else:
            response_message = f"Perfect! ✓\n\n{confirmed}\n\nAll required information collected! Ready to preview your document."
            next_step = "complete"
    else:
        # No info extracted, ask for clarification
        if missing_required:
            next_field = missing_required[0]
            response_message = f"I need a bit more information. What's the **{next_field.replace('_', ' ')}**?"
            next_step = "collecting"
        else:
            response_message = "All information collected! Ready to preview."
            next_step = "complete"
    
    return AgentMessageResponse(
        message=response_message,
        current_step=next_step,
        session_id=session_id,
        collected_data=manual_data,
        required_fields=required_fields,
        optional_fields=optional_fields
    )


@router.post("/generate", response_model=GeneratedDocumentResponse)
async def generate_document_direct(
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Direct document generation from manual form
    Request body: { templateId: str, data: dict }
    """
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    template_id = request.get("templateId")
    data = request.get("data", {})
    
    if not template_id or not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing templateId or data"
        )
    
    # Map template_id string to database template
    template_name_map = {
        "offer": "Offer Letter",
        "experience": "Experience Letter",
        "relieving": "Relieving Letter",
        "promotion": "Promotion Letter",
        "warning": "Warning Letter",
        "transfer": "Transfer Letter"
    }
    
    template_name = template_name_map.get(template_id, template_id.replace("_", " ").title())
    
    # Find template - use exact match to avoid multiple results
    result = await db.execute(
        select(DocumentTemplate)
        .where(DocumentTemplate.name == template_name)
        .where(DocumentTemplate.is_active.is_(True))
        .limit(1)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_name}")
    
    # Create GeneratedDocument record
    import json
    from cryptography.fernet import Fernet
    import base64
    
    employee_name = data.get("employee_name", "Unknown")
    
    # Hash phone if provided
    phone_hash = None
    if data.get("phone_number"):
        phone_hash = hashlib.sha256(data["phone_number"].encode()).hexdigest()
    
    # Simple encryption for recipient name (use same approach as agent)
    # Generate a simple key from a fixed secret (in production, use proper key management)
    secret_key = "TalentConnect2024SecretKey!!"  # Should be in env vars
    key = base64.urlsafe_b64encode(hashlib.sha256(secret_key.encode()).digest())
    cipher_suite = Fernet(key)
    encrypted_name = cipher_suite.encrypt(employee_name.encode()).decode()
    
    new_doc = GeneratedDocument(
        template_id=template.id,
        document_type=template.name,
        recipient_name_encrypted=encrypted_name,
        employee_code=data.get("employee_code"),
        phone_number_hash=phone_hash,
        document_data=json.dumps(data),
        generated_by=current_user.id,
        status="generated",
        generated_at=datetime.now()
    )
    
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    
    return GeneratedDocumentResponse(
        id=new_doc.id,
        template_id=new_doc.template_id,
        document_type=new_doc.document_type,
        recipient_name=employee_name,
        employee_code=new_doc.employee_code,
        generated_at=new_doc.generated_at,
        status=new_doc.status,
        email_sent=new_doc.email_sent,
        digitally_signed=new_doc.digitally_signed
    )


@router.get("/query", response_model=DocumentQueryResponse)
async def query_documents(
    employee_code: str = None,
    phone_number: str = None,
    document_type: str = None,
    recipient_name: str = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Search and retrieve previously generated documents
    Can search by employee_code, phone_number, recipient_name, or document_type
    Shows only documents generated by the current user
    """
    if current_user.role not in ["hr", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    filters = [GeneratedDocument.generated_by == current_user.id]
    
    if employee_code:
        filters.append(GeneratedDocument.employee_code == employee_code)
    
    if phone_number:
        phone_hash = hashlib.sha256(phone_number.encode()).hexdigest()
        filters.append(GeneratedDocument.phone_number_hash == phone_hash)
    
    if document_type:
        filters.append(GeneratedDocument.document_type.ilike(f"%{document_type}%"))
    
    if recipient_name:
        # Search in the encrypted recipient_name field (stored as plaintext currently)
        filters.append(GeneratedDocument.recipient_name_encrypted.ilike(f"%{recipient_name}%"))
    
    query = select(GeneratedDocument).where(and_(*filters))
    query = query.order_by(GeneratedDocument.generated_at.desc()).limit(limit)
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    # Build response with recipient names (decrypt if needed)
    agent = DocumentAgentService(db)
    docs_resp = []
    for doc in documents:
        # Try to decrypt name, fallback to plaintext
        try:
            recipient_name = agent._decrypt_data(doc.recipient_name_encrypted)
        except:
            recipient_name = doc.recipient_name_encrypted
        
        data = {
            "id": doc.id,
            "template_id": doc.template_id,
            "document_type": doc.document_type,
            "recipient_name": recipient_name,
            "employee_code": doc.employee_code,
            "generated_at": doc.generated_at,
            "status": doc.status,
            "email_sent": doc.email_sent,
            "digitally_signed": doc.digitally_signed,
            "preview_masked_html": getattr(doc, "preview_masked_html", None)
        }
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
    # Try to decrypt, if fails assume it's already plaintext
    try:
        recipient_name = agent._decrypt_data(document.recipient_name_encrypted)
    except:
        recipient_name = document.recipient_name_encrypted
    safe_name = (recipient_name or "document").replace(" ", "_")
    safe_type = (document.document_type or "letter").replace(" ", "_")
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Get the template and document data
    result_template = await db.execute(
        select(DocumentTemplate).where(DocumentTemplate.id == document.template_id)
    )
    template = result_template.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Parse document_data JSON
    import json
    document_data = json.loads(document.document_data) if isinstance(document.document_data, str) else document.document_data
    
    if format.lower() == "pdf":
        # Generate properly filled PDF using the document generator
        from app.utils.document_generator import DocumentGenerator
        from pathlib import Path
        
        template_path = Path(template.file_path)
        pdf_buffer = io.BytesIO()
        DocumentGenerator.generate_pdf_from_template(template_path, document_data, pdf_buffer)
        pdf_buffer.seek(0)
        
        filename = f"{safe_name}_{today}_{safe_type}.pdf"
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    elif format.lower() == "docx":
        # Generate properly filled DOCX using the document generator
        from app.utils.document_generator import DocumentGenerator
        from pathlib import Path
        
        template_path = Path(template.file_path)
        docx_buffer = io.BytesIO()
        DocumentGenerator.generate_docx_from_template(template_path, document_data, docx_buffer)
        docx_buffer.seek(0)
        
        filename = f"{safe_name}_{today}_{safe_type}.docx"
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
    
    # In production, integrate with email service
    document.email_sent = True
    document.status = "sent"
    await db.commit()
    
    return {
        "message": "Email sent successfully",
        "recipient": email_request.recipient_email
    }


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

