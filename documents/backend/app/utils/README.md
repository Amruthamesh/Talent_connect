# Document Generation Utils

## Overview

This directory contains utility modules for document generation, PII protection, and data validation in the Talent Connect system.

## Modules

### 1. `document_generator.py`

**Purpose:** Generate PDF and DOCX documents from templates with data replacement and signature embedding.

**Key Features:**
- ✅ PDF generation using reportlab
- ✅ DOCX generation using python-docx
- ✅ Template-based placeholder replacement
- ✅ E-signature image embedding
- ✅ Multiple placeholder format support

**Classes:**
- `DocumentGenerator` - Main class for document generation

**Methods:**

#### `generate_pdf_from_template(template_path, data, output_buffer)`
Generates PDF from template file with data filling.

**Parameters:**
- `template_path` (Path): Path to PDF template file
- `data` (Dict[str, Any]): Dictionary with field values
- `output_buffer` (BytesIO): Buffer to write PDF to

**Data Fields:**
- Required fields defined by template
- Optional: `signatory_signature` (base64 image) - replaces name/designation

**Signature Handling:**
- If `signatory_signature` is present in data:
  - Signature image is embedded in PDF
  - `signatory_name` and `signatory_designation` should be "skip" to avoid duplication
  - Signature replaces placeholder text automatically
- Image is decoded from base64 and embedded at proper size (2.5" x 1.2")
- Positioned after "Sincerely," line or at end of document

**Example:**
```python
from pathlib import Path
import io

template_path = Path("templates/Offer_Letter.pdf")
data = {
    "employee_name": "John Doe",
    "designation": "Senior Engineer",
    "salary": "120000",
    "signatory_signature": "iVBORw0KGgoAAAANS...",  # base64 image
    "signatory_name": "skip",  # Don't show text
    "signatory_designation": "skip"
}

pdf_buffer = io.BytesIO()
DocumentGenerator.generate_pdf_from_template(template_path, data, pdf_buffer)
```

#### `generate_docx_from_template(template_path, data, output_buffer)`
Generates DOCX from template file with data filling.

**Parameters:**
- `template_path` (Path): Path to PDF template (read as text)
- `data` (Dict[str, Any]): Dictionary with field values
- `output_buffer` (BytesIO): Buffer to write DOCX to

**Signature Handling:**
- Signature embedded as inline image in document
- Similar logic to PDF generation

#### `_replace_placeholders(template_text, data)`
Internal method to replace placeholders with actual values.

**Placeholder Formats Supported:**
- `[field_name]` - Exact match
- `[FIELD_NAME]` - Uppercase
- `[Field_Name]` - Title case
- `[field name]` - With spaces
- `[FIELD NAME]` - Spaces + uppercase
- `[Field Name]` - Spaces + title case

**Special Field Handling:**
- `employee_name` → Also replaces `[Name]`
- `designation` → Also replaces `[Position]`, `[Job Title]`
- `joining_date` → Also replaces `[Date of Joining]`, `[Start Date]`
- `salary` → Also replaces `[CTC]`, `[Annual CTC]`
- `signatory_name` → Value "skip" replaced with empty string
- `signatory_designation` → Value "skip" replaced with empty string

---

### 2. `field_validators.py`

**Purpose:** Validate and provide hints for document field values.

**Key Features:**
- Field type detection (email, phone, date, etc.)
- Format validation
- User-friendly input hints

**Classes:**
- `FieldValidator` - Validation utilities

**Methods:**

#### `validate_field(field_name, value)`
Validates a field value based on its type.

**Returns:** `(bool, str)` - (is_valid, error_message)

**Validation Rules:**
- Email: RFC 5322 format
- Phone: Digits, spaces, hyphens, + allowed
- Date: Multiple formats supported (YYYY-MM-DD, DD/MM/YYYY, etc.)
- Salary: Numeric values only
- Names: Letters and spaces only

#### `get_field_hint(field_name)`
Returns user-friendly input hint for a field.

**Example:**
```python
hint = FieldValidator.get_field_hint("email")
# Returns: "Format: user@company.com"
```

---

### 3. `pii_protector.py` (Future)

**Purpose:** PII protection utilities for data encryption, hashing, and masking.

**Planned Features:**
- Fernet encryption for sensitive fields
- SHA256 hashing for searchable fields
- Automatic PII detection and masking
- Configurable PII field lists

---

## Usage Examples

### Generate Offer Letter with Signature

```python
from app.utils.document_generator import DocumentGenerator
from pathlib import Path
import io

# Prepare data (typically from CSV or form)
offer_data = {
    "company_name": "DHL IT Services",
    "company_address": "Chennai One IT SEZ",
    "contact_info": "+91-80-12345678 | hr@dhl.com",
    "employee_name": "Amrutha Ramesh",
    "designation": "Senior Software Engineer",
    "joining_date": "01/12/2024",
    "salary": "120000",
    "offer_acceptance_date": "30/11/2024",
    "signatory_signature": "/9j/4AAQSkZJRg...",  # base64 from upload
    "signatory_name": "skip",  # Skip text name
    "signatory_designation": "skip",  # Skip text designation
    "employee_code": "EMP-1001",
    "phone_number": "+91-9876543210",
    "email": "amrutha@example.com"
}

# Generate PDF
template_path = Path("Corporate_HR_Letter_Templates_ZIP/Offer_Letter.pdf")
pdf_buffer = io.BytesIO()

DocumentGenerator.generate_pdf_from_template(
    template_path,
    offer_data,
    pdf_buffer
)

# Save or send PDF
with open("offer_letter.pdf", "wb") as f:
    pdf_buffer.seek(0)
    f.write(pdf_buffer.read())
```

### Validate Fields Before Generation

```python
from app.utils.field_validators import FieldValidator

# Validate email
is_valid, error_msg = FieldValidator.validate_field("email", "john@company.com")
if not is_valid:
    print(f"Error: {error_msg}")

# Validate phone
is_valid, error_msg = FieldValidator.validate_field("phone_number", "+91-9876543210")
if not is_valid:
    print(f"Error: {error_msg}")
```

---

## PII Protection Architecture

### Encrypted Fields (Fernet)
- `recipient_name` - Encrypted in database, decrypted for display/download

### Hashed Fields (SHA256)
- `phone_number` - One-way hash for search without storing plaintext
- `email` - One-way hash for search without storing plaintext

### Masked Preview
- `preview_masked_html` - PII replaced with `[PII Protected]` for safe display

### Data Flow

```
1. CSV Upload / Manual Entry
   ↓
2. Signature Upload (optional)
   ↓ (stored in session context)
3. Document Generation
   ↓ (signature added to row_data if available)
4. Storage:
   - recipient_name: Encrypted (Fernet)
   - phone/email: Hashed (SHA256)
   - preview_masked_html: PII masked
   - document_data: Encrypted with signature
   ↓
5. Query/Display:
   - Decrypt recipient_name for display
   - Show masked preview (safe)
   ↓
6. Download:
   - Decrypt document_data
   - Regenerate PDF/DOCX with signature
   - Serve with filename: {name}_{date}_{type}.{ext}
```

---

## Signature Workflow

### CSV Upload with Signature

**Backend Flow (`document_agent.py`):**
1. User uploads signature → stored in session context
2. User uploads CSV file
3. For each row:
   ```python
   # Retrieve signature from context
   global_sig_b64 = ctx.get("manual_data", {}).get("signatory_signature")
   
   # Apply to row data
   if global_sig_b64:
       row_data["signatory_signature"] = global_sig_b64
       row_data["signatory_name"] = "skip"  # Don't show text
       row_data["signatory_designation"] = "skip"
   
   # Store with document
   doc.document_data = row_data  # Includes signature
   ```

4. On download: DocumentGenerator uses `document_data` including signature

**Frontend Flow:**
1. Signature upload button below CSV upload
2. File validation (PNG, JPG, JPEG only)
3. Upload to `/documents/agent/upload-signature`
4. CSV upload includes signature reference
5. Preview shows masked data (no signature visible - text only)
6. Download regenerates with embedded signature image

---

## Common Issues & Solutions

### Signature Not Appearing

**Problem:** Signature uploaded but not showing in PDF
**Cause:** CSV has `signatory_name` and `signatory_designation` values
**Solution:** Backend now FORCES these to "skip" when signature present (line 583)

**Verification:**
```python
# Check database
SELECT id, document_data FROM generated_documents WHERE id = X;
# Should contain: "signatory_signature": "base64data...", "signatory_name": "skip"
```

### Placeholder Not Replaced

**Problem:** `[Employee Name]` still showing in document
**Cause:** Case mismatch or missing field
**Solution:** Use supported placeholder formats or add custom mapping in `_replace_placeholders`

### PII Visible in Preview

**Problem:** Sensitive data showing in preview modal
**Cause:** Using `content` instead of `preview_masked_html`
**Solution:** Always use `preview_masked_html` for UI display

---

## Testing

### Test Signature Embedding
```bash
cd backend
python3 <<EOF
from app.utils.document_generator import DocumentGenerator
from pathlib import Path
import io
import base64

# Read test signature
with open("test_signature.png", "rb") as f:
    sig_b64 = base64.b64encode(f.read()).decode()

data = {
    "employee_name": "Test User",
    "signatory_signature": sig_b64,
    "signatory_name": "skip",
    "signatory_designation": "skip"
}

pdf_buf = io.BytesIO()
DocumentGenerator.generate_pdf_from_template(
    Path("Corporate_HR_Letter_Templates_ZIP/Offer_Letter.pdf"),
    data,
    pdf_buf
)

with open("test_output.pdf", "wb") as f:
    pdf_buf.seek(0)
    f.write(pdf_buf.read())
    
print("✅ Test PDF generated!")
EOF
```

---

## Future Enhancements

1. **Template Versioning**
   - Track template changes
   - Support multiple template versions
   - Migration for legacy documents

2. **Advanced PII Protection**
   - Automatic PII field detection
   - Configurable masking rules
   - Audit logging for decryption events

3. **Signature Validation**
   - Verify image dimensions
   - Check file size limits
   - Support multiple signature formats

4. **Batch Operations**
   - Parallel document generation
   - Progress tracking
   - Error recovery

---

## Maintenance

**Last Updated:** December 1, 2025

**Dependencies:**
- reportlab >= 4.0.0
- python-docx >= 1.0.0
- PyPDF2 >= 3.0.0
- cryptography >= 41.0.0

**Contact:** Development Team
