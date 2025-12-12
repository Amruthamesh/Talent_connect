"""
Document Agent Service - Agentic bot for HR letter generation
Handles conversational flow for template selection, data collection, and document generation
"""
import uuid
import hashlib
import base64
import json
import io
from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from PyPDF2 import PdfReader
            

from app.models.document import DocumentTemplate, DocumentConversation, GeneratedDocument
from cryptography.fernet import Fernet
from app.config import settings
from app.utils.field_validators import FieldValidator
import re


class DocumentAgentService:
    """Agentic bot for conversational document generation"""
    
    DHL_BRANDING = {
        "company_name": "DHL Supply Chain",
        "company_color": "#FFCC00",  # DHL Yellow
        "secondary_color": "#D40511",  # DHL Red
        "logo_url": "/assets/dhl-logo.png",
        "letterhead_template": "dhl_official"
    }
    
    CONVERSATION_STEPS = {
        "initial": "greeting",
        "template_selection": "selecting_letter_type",
        "input_method": "choosing_data_input",
        "csv_upload": "uploading_data",
        "preview": "reviewing_document",
        "complete": "finished"
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # Generate proper Fernet key from SECRET_KEY
        key_material = settings.SECRET_KEY.encode()
        hashed_key = hashlib.sha256(key_material).digest()
        fernet_key = base64.urlsafe_b64encode(hashed_key)
        self.cipher = Fernet(fernet_key)
        
        # Template directory and file mapping for PDF templates
        self.templates_dir = Path(__file__).parent.parent.parent / "Corporate_HR_Letter_Templates_ZIP"
        self.template_file_map = {
            "offer letter": "Offer_Letter.pdf",
            "experience letter": "Experience_Letter.pdf",
            "relieving letter": "Relieving_Letter.pdf",
            "confirmation letter": "Probation_Confirmation_Letter.pdf",
            "bonus letter": "Bonus_Letter.pdf",
            "termination letter": "Termination_Letter.pdf",
            # Fallback for templates without PDF files
            "appointment letter": "appointment_letter.pdf",
            "promotion letter": "promotion_letter.pdf",
            "salary increment letter": "salary_increment_letter.pdf",
            "transfer letter": "transfer_letter.pdf",
            "warning letter": "warning_letter.pdf",
            "internship offer letter": "internship_offer_letter.pdf"
        }
    
    def _extract_fields_from_pdf(self, template_name: str) -> tuple[list, list]:
        """Extract actual placeholder fields from PDF template"""
        template_filename = self.template_file_map.get(template_name.lower(), "")
        template_path = self.templates_dir / template_filename
        
        if not template_path.exists():
            # PDF doesn't exist, return empty lists to use database fields
            return [], []
        
        try:
            # Read PDF and extract text
            reader = PdfReader(str(template_path))
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            
            # Find all [PLACEHOLDER] patterns
            placeholders = re.findall(r'\[([^\]]+)\]', text)
            
            # Clean placeholders (remove extra whitespace and newlines)
            placeholders = [p.replace('\n', ' ').strip() for p in placeholders]
            
            # Field name mapping: PDF placeholder -> database field name
            field_mapping = {
                "employee name": "employee_name",
                "candidate name": "employee_name",
                "name": "employee_name",
                "designation": "designation",
                "position": "designation",
                "date of joining": "joining_date",
                "joining date": "joining_date",
                "start date": "joining_date",
                "ctc": "salary",
                "salary": "salary",
                "annual ctc": "salary",
                "employee code": "employee_code",
                "emp code": "employee_code",
                "department": "department",
                "location": "location",
                "office location": "location",
                "last working date": "last_working_date",
                "relieving date": "last_working_date",
                "confirmation date": "confirmation_date",
                "offer acceptance date": "offer_acceptance_date",
                "current designation": "current_designation",
                "new designation": "new_designation",
                "new salary": "new_salary",
                "effective date": "effective_date",
                "increment amount": "increment_amount",
                "new department": "new_department",
                "reporting manager": "reporting_manager",
                "probation period": "probation_period",
                "phone number": "phone_number",
                "email": "email",
                "new location": "new_location",
                "transfer date": "transfer_date",
                "reason": "reason",
                "issue date": "issue_date",
                "warning type": "warning_type",
                "incident date": "incident_date",
                "responsibilities": "responsibilities",
                "achievements": "achievements",
                "skills": "skills",
                "notice period served": "notice_period_served",
                "reason for leaving": "reason_for_leaving",
                "probation feedback": "probation_feedback",
                "signatory name": "signatory_name",
                "signatory designation": "signatory_designation",
                "signatory signature": "signatory_signature",
                "signature": "signatory_signature",
                "e-signature": "signatory_signature",
                "esignature": "signatory_signature",
                "company name": "company_name",
                "company address": "company_address",
                "company logo": "company_logo",
                "contact info": "contact_info",
                "date": "date",
                # Additional placeholders from PDFs
                "bonus amount": "bonus_amount",
                "month": "month",
                "he/she/they": "pronoun_subject",
                "his/her/their": "pronoun_possessive",
                "reason for termination": "reason_for_termination",
                "termination date": "termination_date",
                # Handle multi-line placeholders
                "company\nname": "company_name",
                "date\nof joining": "joining_date"
            }
            
            # Convert placeholders to field names - DON'T SKIP ANY
            required_fields = []
            for placeholder in placeholders:
                placeholder_lower = placeholder.lower().strip()
                field_name = field_mapping.get(placeholder_lower, placeholder_lower.replace(' ', '_'))
                if field_name not in required_fields:
                    required_fields.append(field_name)
            
            print(f"🔍 Extracted {len(required_fields)} fields from PDF: {required_fields}")
            return required_fields, []  # No optional fields for now
            
        except Exception as e:
            print(f"⚠️ Error extracting fields from PDF: {e}")
            return [], []
    
    async def start_conversation(self, user_id: int) -> Dict[str, Any]:
        """Start a new document generation conversation"""
        session_id = str(uuid.uuid4())
        
        conversation = DocumentConversation(
            session_id=session_id,
            user_id=user_id,
            current_step="initial",
            context={}
        )
        self.db.add(conversation)
        await self.db.commit()
        
        # Get available templates
        templates_result = await self.db.execute(
            select(DocumentTemplate).where(DocumentTemplate.is_active.is_(True))
        )
        templates = templates_result.scalars().all()
        
        template_options = [
            {
                "id": t.id,
                "name": t.name,
                "category": t.category,
                "description": t.description
            }
            for t in templates
        ]
        
        return {
            "session_id": session_id,
            "message": "Hello! I'm your HR Document Assistant. I'll help you generate professional letters using DHL branding. Which type of letter do you need today?",
            "current_step": "initial",
            "templates": template_options,
            "next_step": "template_selection",
            "requires_upload": False
        }
    
    async def process_template_selection(
        self, session_id: str, template_id: int
    ) -> Dict[str, Any]:
        """Handle template selection"""
        print(f"🔍 DEBUG process_template_selection: session_id={session_id}, template_id={template_id}")
        conversation = await self._get_conversation(session_id)
        print(f"🔍 DEBUG conversation.id={conversation.id}, current selected_template_id={conversation.selected_template_id}")
        template = await self._get_template(template_id)
        print(f"🔍 DEBUG template found: id={template.id}, name='{template.name}'")
        
        conversation.selected_template_id = template_id
        conversation.current_step = "input_method"
        print(f"🔍 DEBUG After assignment: selected_template_id={conversation.selected_template_id}")
        
        # Extract actual fields from PDF template (if exists)
        pdf_required, pdf_optional = self._extract_fields_from_pdf(template.name)
        
        # Use PDF fields if available, otherwise fall back to database fields
        if pdf_required:
            required_fields = pdf_required
            optional_fields = pdf_optional
            print(f"🔍 Using PDF-extracted fields: {required_fields}")
        else:
            required_fields = template.required_fields
            optional_fields = template.optional_fields
            print(f"🔍 Using database fields: {required_fields}")
        
        # Update context - need to reassign to trigger SQLAlchemy update
        new_context = dict(conversation.context) if conversation.context else {}
        new_context["template_name"] = template.name
        new_context["required_fields"] = required_fields
        new_context["optional_fields"] = optional_fields
        conversation.context = new_context
        flag_modified(conversation, "context")
        
        await self.db.commit()
        await self.db.refresh(conversation)
        print(f"🔍 DEBUG After commit: selected_template_id={conversation.selected_template_id}")
        
        return {
            "session_id": session_id,
            "message": f"Great! You've selected '{template.name}'. \n\nThis template requires the following information: {', '.join(required_fields)}.\n\nHow would you like to provide the data?",
            "current_step": "input_method",
            "required_fields": required_fields,
            "optional_fields": optional_fields,
            "options": [
                {
                    "id": "manual_entry",
                    "label": "Fill field-by-field",
                    "description": "I'll guide you through each field one by one"
                },
                {
                    "id": "upload_csv",
                    "label": "Upload CSV file",
                    "description": "I have a CSV file ready with employee data"
                },
                {
                    "id": "download_template",
                    "label": "Download CSV template",
                    "description": "Download template to fill and upload back"
                }
            ],
            "requires_upload": False
        }
    
    async def process_input_method(
        self, session_id: str, method: str
    ) -> Dict[str, Any]:
        """Handle input method selection"""
        conversation = await self._get_conversation(session_id)
        conversation.input_method = method
        
        if method == "manual_entry":
            # Start manual field-by-field entry
            conversation.current_step = "manual_entry"
            await self.db.commit()
            
            required_fields = conversation.context.get("required_fields", [])
            optional_fields = conversation.context.get("optional_fields", [])
            
            if not required_fields:
                return {
                    "session_id": session_id,
                    "message": "No fields configured for this template.",
                    "current_step": "error"
                }
            
            # Start with first required field
            first_field = required_fields[0]
            
            return {
                "session_id": session_id,
                "message": f"Perfect! Let's fill this out step by step. I'll ask for each field one at a time.\\n\\nFirst, please provide **{first_field.replace('_', ' ')}**:",
                "current_step": "manual_entry",
                "current_field": first_field,
                "required_fields": required_fields,
                "optional_fields": optional_fields
            }
        
        elif method == "download_template":
            # Generate CSV template
            conversation.current_step = "csv_upload"
            await self.db.commit()
            
            template = await self._get_template(conversation.selected_template_id)
            csv_url = await self._generate_csv_template(template)
            
            return {
                "session_id": session_id,
                "message": "I've prepared a CSV template with all the required columns. Please download it, fill in the details, and upload it back.",
                "current_step": "csv_upload",
                "csv_download_url": csv_url,
                "requires_upload": True
            }
        else:  # upload_csv
            conversation.current_step = "csv_upload"
            await self.db.commit()
            
            return {
                "session_id": session_id,
                "message": "Perfect! Please upload your CSV file with the employee data.",
                "current_step": "csv_upload",
                "requires_upload": True
            }
    
    async def process_manual_field(
        self, session_id: str, field_name: str, field_value: str
    ) -> Dict[str, Any]:
        """Process a single field input during manual entry with validation"""
        conversation = await self._get_conversation(session_id)
        
        print(f"🔍 DEBUG process_manual_field: field_name={field_name}, field_value={field_value}")
        print(f"🔍 DEBUG current context: {conversation.context}")
        
        # Validate the field value
        is_valid, error_message = FieldValidator.validate_field(field_name, field_value)
        
        print(f"🔍 DEBUG validation result: is_valid={is_valid}, error={error_message}")
        
        if not is_valid:
            # Return validation error with hint
            hint = FieldValidator.get_field_hint(field_name)
            return {
                "session_id": session_id,
                "message": f"❌ **Validation Error**\n\n{error_message}\n\n**Hint**: {hint}\n\nPlease enter **{field_name.replace('_', ' ')}** again:",
                "current_step": "manual_entry",
                "validation_error": True,
                "field_name": field_name,
                "error": error_message,
                "hint": hint
            }
        
        # Get current context and update it properly
        ctx = dict(conversation.context) if conversation.context else {}
        
        print(f"🔍 DEBUG ctx before update: {ctx}")
        
        # Initialize manual_data and validation_status if not exists
        if "manual_data" not in ctx:
            ctx["manual_data"] = {}
        if "validation_status" not in ctx:
            ctx["validation_status"] = {}
        
        # Store the field value and mark as valid
        ctx["manual_data"][field_name] = field_value
        ctx["validation_status"][field_name] = "valid"
        
        print(f"🔍 DEBUG ctx after update: {ctx}")
        print(f"🔍 DEBUG manual_data now has: {ctx['manual_data']}")
        
        conversation.context = ctx  # Reassign to trigger update
        flag_modified(conversation, "context")  # Force SQLAlchemy to detect the change
        await self.db.commit()  # Commit immediately to persist changes
        
        print("🔍 DEBUG After commit - context should be saved")
        
        # Get required and optional fields
        required_fields = ctx.get("required_fields", [])
        optional_fields = ctx.get("optional_fields", [])
        all_fields = required_fields + optional_fields
        
        # Find next field to ask for
        filled_fields = list(ctx["manual_data"].keys())
        remaining_fields = [f for f in all_fields if f not in filled_fields]
        
        print(f"🔍 DEBUG filled_fields: {filled_fields}, remaining: {remaining_fields}")
        
        if remaining_fields:
            next_field = remaining_fields[0]
            is_required = next_field in required_fields
            hint = FieldValidator.get_field_hint(next_field)
            
            # Check if next field is signatory_signature (file upload)
            if next_field == "signatory_signature":
                return {
                    "session_id": session_id,
                    "message": f"✓ Got it! **{field_name.replace('_', ' ')}**: {field_value}\n\n📝 Next, please **upload the signatory's e-signature image** (PNG, JPG, or JPEG format).",
                    "current_step": "manual_entry",
                    "current_field": next_field,
                    "required_fields": required_fields,
                    "optional_fields": optional_fields,
                    "requires_file_upload": True,
                    "file_upload_type": "signature",
                    "hint": "Upload a clear signature image in PNG or JPG format"
                }
            
            # Already committed above, no need to commit again
            
            return {
                "session_id": session_id,
                "message": f"✓ Got it! **{field_name.replace('_', ' ')}**: {field_value}\n\nNext, please provide **{next_field.replace('_', ' ')}**" + 
                          (" (required)" if is_required else " (optional - type 'skip' to skip)") +
                          f"\n\n💡 **Hint**: {hint}",
                "current_step": "manual_entry",
                "current_field": next_field,
                "required_fields": required_fields,
                "optional_fields": optional_fields,
                "hint": hint
            }
        else:
            # All fields collected
            conversation.current_step = "manual_complete"
            flag_modified(conversation, "current_step")
            await self.db.commit()
            
            return {
                "session_id": session_id,
                "message": "✓ Perfect! All fields validated successfully.\n\nReady to preview and generate your document.",
                "current_step": "manual_complete",
                "all_fields_collected": True,
                "total_fields": len(all_fields),
                "filled_fields": len(filled_fields) + 1
            }
    
    async def process_manual_complete(
        self, session_id: str, action: str, user_id: int
    ) -> Dict[str, Any]:
        """Handle completion of manual entry - add another or generate"""
        conversation = await self._get_conversation(session_id)
        ctx = dict(conversation.context) if conversation.context else {}
        
        if action == "add_another":
            # Save current entry and reset for new one
            if "all_manual_entries" not in ctx:
                ctx["all_manual_entries"] = []
            
            ctx["all_manual_entries"].append(ctx.get("manual_data", {}))
            ctx["manual_data"] = {}
            conversation.context = ctx
            conversation.current_step = "manual_entry"
            await self.db.commit()
            
            required_fields = ctx.get("required_fields", [])
            first_field = required_fields[0] if required_fields else None
            
            return {
                "session_id": session_id,
                "message": f"Great! You've added {len(ctx['all_manual_entries'])} letter(s) so far.\n\nLet's add another one. First field:",
                "current_step": "manual_entry",
                "current_field": first_field,
                "required_fields": required_fields,
                "optional_fields": ctx.get("optional_fields", [])
            }
        else:  # generate
            # Collect all entries
            all_entries = ctx.get("all_manual_entries", [])
            all_entries.append(ctx.get("manual_data", {}))
            
            # Generate documents
            template = await self._get_template(conversation.selected_template_id)
            document_ids = []
            preview_data = []
            
            for idx, entry_data in enumerate(all_entries, 1):
                # Generate document content
                doc_content = self._generate_document_content(template, entry_data)
                
                # Create document record
                doc = GeneratedDocument(
                    generated_by=user_id,
                    template_id=template.id,
                    document_type=template.name.lower().replace(' ', '_'),
                    recipient_name_encrypted=entry_data.get('employee_name', 'Unknown'),
                    content=doc_content,
                    document_data=entry_data,
                    status="generated"
                )
                self.db.add(doc)
                await self.db.flush()
                
                document_ids.append(doc.id)
                preview_data.append({
                    "id": doc.id,
                    "row_number": idx,
                    "employee_name": entry_data.get("employee_name", "Unknown"),
                    "preview_html": self._mask_pii_in_content(doc_content, entry_data),
                    "document_type": template.name
                })
            
            await self.db.commit()
            conversation.current_step = "completed"
            await self.db.commit()
            
            return {
                "session_id": session_id,
                "message": f"✅ Successfully generated **{len(document_ids)} {template.name}** letters with DHL branding!\n\nBelow is a preview with sensitive information masked for security. You can download individual letters or all as a ZIP file.",
                "current_step": "completed",
                "generated_count": len(document_ids),
                "document_ids": document_ids,
                "preview_data": preview_data,
                "template_name": template.name
            }
    
    async def process_csv_upload(
        self, session_id: str, csv_data: List[Dict[str, Any]], user_id: int
    ) -> Dict[str, Any]:
        """Process uploaded CSV data and generate documents with preview"""
        conversation = await self._get_conversation(session_id)
        template = await self._get_template(conversation.selected_template_id)
        
        # Normalize CSV keys using common synonyms before validation
        csv_data = [self._normalize_row_keys(row) for row in csv_data]
        # Validate CSV columns
        validation_errors = await self._validate_csv_data(csv_data, template)
        if validation_errors:
            return {
                "session_id": session_id,
                "message": f"⚠️ CSV validation failed:\n\n{chr(10).join(['• ' + e for e in validation_errors])}\n\nPlease fix these issues and upload again.",
                "current_step": "csv_upload",
                "requires_upload": True
            }
        
        # Generate documents for each row
        generated_docs = []
        preview_data = []
        
        # Resolve global signature from session context if present
        ctx = dict(conversation.context) if conversation.context else {}
        global_sig_b64 = None
        manual_data = ctx.get("manual_data", {})
        if manual_data.get("signatory_signature"):
            global_sig_b64 = manual_data.get("signatory_signature")

        for idx, row_data in enumerate(csv_data, 1):
            # Normalize/resolve signature for this row
            sig_b64 = row_data.get("signatory_signature")
            sig_url = row_data.get("signatory_signature_url")
            try:
                if not sig_b64 and sig_url:
                    # Fetch image from URL and convert to base64
                    import requests, base64
                    resp = requests.get(sig_url, timeout=10)
                    resp.raise_for_status()
                    sig_b64 = base64.b64encode(resp.content).decode("utf-8")
                elif sig_b64 and sig_b64.startswith("data:image"):
                    # Strip data URL header
                    sig_b64 = sig_b64.split(",", 1)[1]
            except Exception as e:
                print(f"⚠️ Error resolving signature for row {idx}: {e}")
                sig_b64 = sig_b64 or global_sig_b64

            if not sig_b64 and global_sig_b64:
                sig_b64 = global_sig_b64
            if sig_b64:
                row_data["signatory_signature"] = sig_b64
                # Optional: auto-skip text fields
                row_data.setdefault("signatory_name", "")
                row_data.setdefault("signatory_designation", "")
            # Generate document content
            doc_content = self._generate_document_content(template, row_data)
            
            # Create document record
            doc = GeneratedDocument(
                generated_by=user_id,
                template_id=template.id,
                document_type=template.name.lower().replace(' ', '_'),
                recipient_name_encrypted=row_data.get('employee_name', 'Unknown'),
                content=doc_content,  # Will be encrypted by model
                document_data=row_data,  # Will be encrypted by model
                status="generated"
            )
            self.db.add(doc)
            await self.db.flush()
            
            generated_docs.append(doc)
            
            # Create preview with PII masking
            # Build masked preview html (basic masking for name, phone, email)
            def _mask_text(text: str) -> str:
                import re
                if not text:
                    return text
                masked = text
                # Mask emails: keep first char and domain, replace middle
                masked = re.sub(r'([a-zA-Z0-9_.%+-])([a-zA-Z0-9_.%+-]*)(@[^\s<>"]+)', r'\1***\3', masked)
                # Mask phone numbers: show last 4 digits
                masked = re.sub(r'(\+?\d[\d\- ]{6,}?(\d{4}))', lambda m: '***' + m.group(2), masked)
                # Mask names present in data (simple replace)
                name = row_data.get('employee_name')
                if name and name.strip():
                    safe = name.split(' ')[0]
                    masked = masked.replace(name, f"{safe} ***")
                return masked

            preview_html = self._mask_pii_in_content(doc_content, row_data)
            preview_masked_html = _mask_text(preview_html)

            preview_data.append({
                "id": doc.id,
                "row_number": idx,
                "employee_name": row_data.get("employee_name", "Unknown"),
                "preview_html": preview_html,
                "preview_masked_html": preview_masked_html,
                "document_type": template.name
            })

            # Persist masked preview and hashes
            import hashlib
            phone = (row_data.get('phone_number') or '').strip()
            email = (row_data.get('email') or '').strip()
            doc.preview_masked_html = preview_masked_html
            doc.phone_number_hash = hashlib.sha256(phone.encode()).hexdigest() if phone else None
            doc.email_hash = hashlib.sha256(email.encode()).hexdigest() if email else None
            await self.db.flush()
        
        conversation.current_step = "preview"
        ctx_csv = dict(conversation.context) if conversation.context else {}
        ctx_csv["generated_document_ids"] = [d.id for d in generated_docs]
        conversation.context = ctx_csv
        await self.db.commit()
        
        return {
            "session_id": session_id,
            "message": f"✅ Successfully generated **{len(generated_docs)} {template.name}** letters with DHL branding!\n\nBelow is a preview with sensitive information masked for security. You can download individual letters or all as a ZIP file.",
            "current_step": "completed",
            "generated_count": len(generated_docs),
            "document_ids": [d.id for d in generated_docs],
            "preview_data": preview_data,
            "template_name": template.name
        }
    
    async def process_signature_upload(
        self, session_id: str, signature_data: bytes, filename: str
    ) -> Dict[str, Any]:
        """Process uploaded e-signature image"""
        conversation = await self._get_conversation(session_id)
        
        # Store signature in context as base64
        signature_base64 = base64.b64encode(signature_data).decode('utf-8')
        
        ctx = dict(conversation.context) if conversation.context else {}
        if "manual_data" not in ctx:
            ctx["manual_data"] = {}
        
        # Store signature
        ctx["manual_data"]["signatory_signature"] = signature_base64
        ctx["validation_status"] = ctx.get("validation_status", {})
        ctx["validation_status"]["signatory_signature"] = "valid"
        
        # Auto-skip signatory_name and signatory_designation since signature contains them
        required_fields = ctx.get("required_fields", [])
        optional_fields = ctx.get("optional_fields", [])
        all_fields = required_fields + optional_fields
        
        if "signatory_name" in all_fields:
            ctx["manual_data"]["signatory_name"] = "skip"
            ctx["validation_status"]["signatory_name"] = "valid"
        if "signatory_designation" in all_fields:
            ctx["manual_data"]["signatory_designation"] = "skip"
            ctx["validation_status"]["signatory_designation"] = "valid"
        
        conversation.context = ctx
        flag_modified(conversation, "context")
        await self.db.commit()
        
        # Find next field (skip signatory name/designation)
        filled_fields = list(ctx["manual_data"].keys())
        remaining_fields = [f for f in all_fields if f not in filled_fields]
        
        if remaining_fields:
            next_field = remaining_fields[0]
            is_required = next_field in required_fields
            hint = FieldValidator.get_field_hint(next_field)
            
            return {
                "session_id": session_id,
                "message": f"✓ E-signature uploaded successfully!\n\nNext, please provide **{next_field.replace('_', ' ')}**" +
                          (" (required)" if is_required else " (optional - type 'skip' to skip)") +
                          f"\n\n💡 **Hint**: {hint}",
                "current_step": "manual_entry",
                "current_field": next_field,
                "required_fields": required_fields,
                "optional_fields": optional_fields,
                "hint": hint
            }
        else:
            # All fields collected
            conversation.current_step = "manual_complete"
            flag_modified(conversation, "current_step")
            await self.db.commit()
            
            return {
                "session_id": session_id,
                "message": "✅ Perfect! All information collected. Generating preview...",
                "current_step": "manual_complete",
                "requires_preview": True
            }
    
    async def _generate_document(
        self, template: DocumentTemplate, data: Dict[str, Any], user_id: int
    ) -> GeneratedDocument:
        """Generate a single document from template and data"""
        # Extract identifier (employee_code or phone_number)
        employee_code = data.get("employee_code") or data.get("emp_code")
        phone_number = data.get("phone_number") or data.get("mobile")
        
        # Hash phone number for privacy
        phone_hash = None
        if phone_number:
            phone_hash = hashlib.sha256(str(phone_number).encode()).hexdigest()
        
        # Encrypt recipient name
        recipient_name = data.get("employee_name") or data.get("candidate_name") or "Unknown"
        encrypted_name = self._encrypt_data(recipient_name)
        
        # Generate file path (would be actual file generation in production)
        file_path = f"documents/{template.name.lower().replace(' ', '_')}/{uuid.uuid4()}.docx"
        file_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        
        doc = GeneratedDocument(
            template_id=template.id,
            employee_code=employee_code,
            phone_number_hash=phone_hash,
            recipient_name_encrypted=encrypted_name,
            document_type=template.name.lower().replace(" ", "_"),
            file_storage_path=self._encrypt_data(file_path),
            file_hash=file_hash,
            generated_by=user_id,
            status="draft"
        )
        
        self.db.add(doc)
        await self.db.flush()
        return doc
    
    async def generate_preview(self, session_id: str) -> Dict[str, Any]:
        """Generate preview HTML of the document with validation"""
        from app.utils.document_generator import DocumentGenerator
        
        conversation = await self._get_conversation(session_id)
        ctx = dict(conversation.context) if conversation.context else {}
        
        # Get collected data
        manual_data = ctx.get("manual_data", {})
        
        # Validate all fields
        validation_errors = {}
        validation_status = ctx.get("validation_status", {})
        
        for field_name, value in manual_data.items():
            is_valid, error_msg = FieldValidator.validate_field(field_name, value)
            if not is_valid:
                validation_errors[field_name] = error_msg
                validation_status[field_name] = "invalid"
            else:
                validation_status[field_name] = "valid"
        
        # Update context with validation status
        ctx["validation_status"] = validation_status
        conversation.context = ctx
        await self.db.commit()
        
        all_valid = len(validation_errors) == 0
        
        if not all_valid:
            return {
                "session_id": session_id,
                "preview_html": "",
                "validation_errors": validation_errors,
                "all_fields_valid": False,
                "collected_data": manual_data
            }
        
        # Generate preview HTML
        conversation = await self._get_conversation(session_id)
        print(f"🔍 DEBUG generate_preview: selected_template_id={conversation.selected_template_id}")
        
        if conversation.selected_template_id is None:
            raise ValueError("No template selected for this conversation")
            
        template = await self._get_template(conversation.selected_template_id)
        template_name_lower = template.name.lower()
        
        # Find matching template file with flexible name matching
        template_filename = ""
        
        # Try exact match first
        if template_name_lower in self.template_file_map:
            template_filename = self.template_file_map[template_name_lower]
        else:
            # Try partial match - find which base template this belongs to
            for base_name, filename in self.template_file_map.items():
                if base_name in template_name_lower:
                    template_filename = filename
                    break
        
        template_path = self.templates_dir / template_filename if template_filename else None
        
        print(f"🔍 DEBUG generate_preview: template.name='{template.name}', lower='{template_name_lower}'")
        print(f"🔍 DEBUG template_filename='{template_filename}'")
        print(f"🔍 DEBUG template_path='{template_path}', exists={template_path.exists() if template_path else 'N/A'}")
        
        try:
            print(f"🔍 DEBUG generate_preview: manual_data = {manual_data}")
            
            if not template_path.exists():
                # Fallback preview
                print(f"🔍 DEBUG Using fallback preview")
                preview_html = self._generate_simple_preview(template, manual_data)
            else:
                print(f"🔍 DEBUG Using PDF-based preview")
                print(f"🔍 DEBUG calling DocumentGenerator.generate_preview_html with data: {manual_data}")
                preview_html = DocumentGenerator.generate_preview_html(template_path, manual_data)
        except Exception as e:
            print(f"🔍 DEBUG Error generating preview: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to simple preview on any error
            preview_html = self._generate_simple_preview(template, manual_data)
        
        return {
            "session_id": session_id,
            "preview_html": preview_html,
            "validation_errors": None,
            "all_fields_valid": True,
            "collected_data": manual_data
        }
    
    async def generate_documents(
        self, session_id: str, user_id: int, output_format: str = "pdf"
    ) -> Dict[str, Any]:
        """Generate final documents in PDF or DOCX format"""
        from app.utils.document_generator import DocumentGenerator
        
        conversation = await self._get_conversation(session_id)
        ctx = dict(conversation.context) if conversation.context else {}
        
        print(f"🔍 DEBUG generate_documents: session_id={session_id}, format={output_format}")
        print(f"🔍 DEBUG context keys: {list(ctx.keys())}")
        print(f"🔍 DEBUG manual_data: {ctx.get('manual_data')}")
        print(f"🔍 DEBUG all_manual_entries: {ctx.get('all_manual_entries')}")
        
        # Get collected data - check both possible locations
        manual_data = ctx.get("manual_data", {})
        all_entries = ctx.get("all_manual_entries", [])
        
        # If we have manual_data but no all_entries, use manual_data
        if manual_data and not all_entries:
            all_entries = [manual_data]
        
        print(f"🔍 DEBUG all_entries to generate: {all_entries}")
        
        if not all_entries:
            raise ValueError("No data collected to generate document")
        
        template = await self._get_template(conversation.selected_template_id)
        
        # Find matching template file with flexible name matching
        template_name_lower = template.name.lower()
        template_filename = ""
        
        # Try exact match first
        if template_name_lower in self.template_file_map:
            template_filename = self.template_file_map[template_name_lower]
        else:
            # Try partial match - find which base template this belongs to
            for base_name, filename in self.template_file_map.items():
                if base_name in template_name_lower:
                    template_filename = filename
                    break
        
        if not template_filename:
            # Fallback to text generation if no PDF found
            template_filename = ""
        
        template_path = self.templates_dir / template_filename if template_filename else None
        
        document_ids = []
        
        for entry_data in all_entries:
            # Debug: Log the data being used for generation
            print(f"🔍 DEBUG: Generating document with data: {entry_data}")
            
            # Generate document in requested format
            output_stream = io.BytesIO()
            
            if template_path.exists():
                if output_format == "pdf":
                    DocumentGenerator.generate_pdf_from_template(
                        template_path, entry_data, output_stream
                    )
                else:  # docx
                    DocumentGenerator.generate_docx_from_template(
                        template_path, entry_data, output_stream
                    )
                
                content = output_stream.getvalue().decode('latin1', errors='ignore')
            else:
                # Fallback text generation
                content = self._generate_document_content(template, entry_data)
            
            # Extract PII for encryption
            recipient_name = entry_data.get("employee_name") or entry_data.get("name") or "Unknown"
            phone = entry_data.get("phone_number") or entry_data.get("phone")
            
            # Create document record
            doc = GeneratedDocument(
                generated_by=user_id,
                template_id=template.id,
                document_type=template.name.lower().replace(' ', '_'),
                employee_code=entry_data.get("employee_code"),
                phone_number_hash=hashlib.sha256(phone.encode()).hexdigest() if phone else None,
                recipient_name_encrypted=self._encrypt_data(recipient_name),
                content=content[:5000],  # Store preview
                document_data=entry_data,
                status="generated",
                file_storage_path=f"documents/{uuid.uuid4()}.{output_format}"
            )
            self.db.add(doc)
            await self.db.flush()
            document_ids.append(doc.id)
        
        await self.db.commit()
        
        return {
            "session_id": session_id,
            "message": f"✅ Successfully generated {len(document_ids)} document(s) in {output_format.upper()} format!\n\nDocuments are now available in your library.",
            "current_step": "completed",
            "generated_count": len(document_ids),
            "document_ids": document_ids
        }
    
    def _generate_simple_preview(self, template: DocumentTemplate, data: Dict[str, Any]) -> str:
        """Generate simple HTML preview when template file not found"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Courier New', monospace; max-width: 800px; margin: 40px auto; padding: 40px; }}
        .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
        .field {{ margin: 15px 0; }}
        .label {{ font-weight: bold; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>{template.name}</h2>
        <p>ABC Corporation</p>
    </div>
    <div class="content">
"""
        for field_name, value in data.items():
            html += f'<div class="field"><span class="label">{field_name.replace("_", " ").title()}:</span> {value}</div>\n'
        
        html += """
    </div>
</body>
</html>
"""
        return html
    
    async def _get_conversation(self, session_id: str) -> DocumentConversation:
        """Get conversation by session ID"""
        result = await self.db.execute(
            select(DocumentConversation).where(
                DocumentConversation.session_id == session_id
            )
        )
        return result.scalar_one()
    
    async def _get_template(self, template_id: int) -> DocumentTemplate:
        """Get template by ID"""
        result = await self.db.execute(
            select(DocumentTemplate).where(DocumentTemplate.id == template_id)
        )
        return result.scalar_one()
    
    async def _validate_csv_data(
        self, csv_data: List[Dict[str, Any]], template: DocumentTemplate
    ) -> List[str]:
        """Validate CSV data against template requirements (lenient with synonyms) and include hints."""
        from app.utils.field_validators import FieldValidator
        errors = []
        if not csv_data:
            return ["CSV file is empty"]

        # Build header set from first row
        first_row = csv_data[0]
        headers = set(first_row.keys())

        # Prefer PDF-extracted fields when available
        pdf_required, pdf_optional = self._extract_fields_from_pdf(template.name)
        required_list = pdf_required or (template.required_fields or [])
        optional_list = pdf_optional or (template.optional_fields or [])

        # Determine missing required after normalization
        missing = []
        for field in required_list:
            if field not in headers:
                missing.append(field)

        # Treat some signatory/company fields as soft optional
        soft_optional = {"signatory_signature", "signatory_name", "signatory_designation", "company_name", "company_address", "contact_info"}
        missing_hard = [m for m in missing if m not in soft_optional]
        if missing_hard:
            # Build per-field messages with examples/hints
            for m in missing_hard:
                hint = FieldValidator.get_field_hint(m)
                errors.append(f"Missing required column: {m} — Hint: {hint}")

        # Optional: warn if known optional fields missing (not blocking)
        optional_missing = [f for f in optional_list if f not in headers]
        if optional_missing:
            errors.append("Missing optional columns (not blocking): " + ", ".join(optional_missing))

        return errors

    def _normalize_row_keys(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize CSV row keys using common synonyms to canonical field names."""
        if not row:
            return row
        mapping = {
            # identity
            "employee_name": "employee_name",
            "candidate_name": "employee_name",
            "name": "employee_name",
            # designation & dept
            "designation": "designation",
            "position": "designation",
            "job_title": "designation",
            "department": "department",
            "dept": "department",
            # dates
            "date_of_joining": "joining_date",
            "joining_date": "joining_date",
            "start_date": "joining_date",
            "last_working_day": "last_working_date",
            # salary
            "ctc": "salary",
            "annual_salary": "salary",
            # identifiers
            "employee_code": "employee_code",
            "emp_code": "employee_code",
            "employee_id": "employee_code",
            # contact
            "phone": "phone_number",
            "mobile": "phone_number",
            "contact_number": "phone_number",
            "email": "email",
            # reporting
            "reporting_manager": "reporting_manager",
            # location
            "location": "location",
            # probation
            "probation_period": "probation_period",
            # signature
            "signatory_signature": "signatory_signature",
            "signatory_signature_url": "signatory_signature_url",
            "signature": "signatory_signature",
            "e-signature": "signatory_signature",
        }
        normalized = {}
        for k, v in row.items():
            key = (k or "").strip()
            canonical = mapping.get(key.lower(), key)
            normalized[canonical] = v
        return normalized
    
    async def _generate_csv_template(self, template: DocumentTemplate) -> str:
        """Generate downloadable CSV template with column headers"""
        # In production, this would generate actual CSV file
        # For now, return a URL path
        return f"/api/v1/documents/templates/{template.id}/csv-template"
    
    def _encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def _generate_document_content(self, template: DocumentTemplate, data: Dict[str, Any]) -> str:
        """Generate document content from PDF template if available, otherwise use fallback"""
        template_name_lower = template.name.lower()
        template_filename = self.template_file_map.get(template_name_lower)
        
        if template_filename:
            template_path = self.templates_dir / template_filename
            
            if template_path.exists():
                try:
                    # Read PDF template
                    reader = PdfReader(str(template_path))
                    
                    # Extract text from all pages
                    template_text = ""
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            template_text += page_text + "\n"
                    
                    # Replace placeholders in the text
                    # PDF templates should have placeholders like {{field_name}}
                    filled_content = template_text
                    for field, value in data.items():
                        placeholder = f"{{{{{field}}}}}"
                        filled_content = filled_content.replace(placeholder, str(value))
                    
                    # Also try without double braces for flexibility
                    for field, value in data.items():
                        placeholder = f"[{field}]"
                        filled_content = filled_content.replace(placeholder, str(value))
                        placeholder_upper = f"[{field.upper()}]"
                        filled_content = filled_content.replace(placeholder_upper, str(value))
                    
                    return f"[PDF Document Generated from {template_filename}]\n\n" + filled_content
                    
                except Exception as e:
                    print(f"Error loading PDF template: {e}")
                    # Fall through to fallback
        
        # Fallback: Generate text content
        content = f"""DHL EXPRESS
{'=' * 60}

{template.name}

Date: {datetime.now().strftime('%B %d, %Y')}

"""
        
        # Fill in data fields
        for field in template.required_fields + template.optional_fields:
            if field in data and data[field]:
                label = field.replace('_', ' ').title()
                content += f"{label}: {data[field]}\n"
        
        content += f"""\n{'=' * 60}

This is an official document from DHL Express.
For any queries, please contact HR Department.

DHL Express | Connecting People, Improving Lives
"""
        
        return content
    
    def _mask_pii_in_content(self, content: str, data: Dict[str, Any]) -> str:
        """Mask PII data in preview for security"""
        masked_content = content
        
        # Define PII fields that should be masked
        pii_fields = [
            "phone_number", "mobile", "email", "aadhar", "pan", "pan_number",
            "salary", "ctc", "account_number", "bank_account", "ifsc",
            "address", "current_address", "permanent_address"
        ]
        
        for field, value in data.items():
            if any(pii in field.lower() for pii in pii_fields) and value:
                str_value = str(value)
                # Mask with asterisks, showing only last 4 chars if applicable
                if len(str_value) > 4:
                    masked_value = "*" * (len(str_value) - 4) + str_value[-4:]
                else:
                    masked_value = "*" * len(str_value)
                masked_content = masked_content.replace(str(value), masked_value)
        
        return masked_content
