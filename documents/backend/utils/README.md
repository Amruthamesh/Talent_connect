# Backend Utils

## field_validators.py
- Validates individual fields with type/format checks.
- Provides user-facing hints via `get_field_hint(field_name)`.
- Used by DocumentAgent to enforce correctness during manual entry.

## document_generator.py
- Generates PDF/DOCX from PDF templates by replacing placeholders.
- Generates HTML preview for display in frontend.
- Supports e-signature embedding (PNG/JPG) via base64.

## pii_protector.py
- Helpers to mask PII (email, phone, salary, etc.).
- Used for `preview_masked_html` storage and query responses.

## storage.py
- Abstractions for storing files (local path/S3) — basic dev impl.

## metadata_* utils
- Resume/document metadata extraction and analysis helpers.

## Usage Patterns
- Prefer `DocumentAgentService` as the orchestrator; call utils through it.
- In dev, preview HTML is stored and served via API; avoid storing raw PII.

## Security Notes
- Names encrypted with Fernet using `SECRET_KEY`.
- Phone/email hashed with SHA-256 for search.
- Always mask PII in previews and responses when possible.
