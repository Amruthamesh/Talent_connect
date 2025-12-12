# Talent Connect Backend

## Overview
- FastAPI application providing HR & Talent modules: Documents, Jobs, Interviews, Auth, Matching.
- Async SQLAlchemy with SQLite (`backend/talent_connect.db`).
- CORS enabled for local development.

## Modules
- **Auth**: JWT-based auth, demo users via `app/db/init_db.py`.
- **Documents**: Templates, agent conversation, CSV upload, preview, generate, library.
- **Jobs**: Upload JDs, generator, matcher.
- **Interviews**: Schedule, lobby, session, summaries.
- **Core/Utils**: Validators, document generation, storage, PII protections.

## Requirements
- Python 3.10+
- `pip install -r requirements.txt`
- Optional: Set API keys in `.env` for AI services.

## Run
```bash
cd backend
./start.sh
# API docs: http://localhost:8000/api/v1/docs
```

## Endpoints (high-level)
- `GET /api/v1/docs` — Swagger UI
- Auth: `POST /api/v1/auth/login`, `GET /api/v1/auth/me`
- Documents:
	- `GET /api/v1/documents/templates`
	- `POST /api/v1/documents/agent/start`
	- `POST /api/v1/documents/agent/select-template`
	- `POST /api/v1/documents/agent/input-method`
	- `POST /api/v1/documents/agent/manual-field`
	- `POST /api/v1/documents/agent/manual-complete`
	- `POST /api/v1/documents/agent/preview`
	- `POST /api/v1/documents/agent/generate`
	- `POST /api/v1/documents/agent/upload-csv`
	- `POST /api/v1/documents/agent/upload-signature`
	- `GET /api/v1/documents/query`
	- `GET /api/v1/documents/{id}` / `{id}/download`
- Jobs/Matcher/Interviews: See `app/api/v1/*.py` and `API_ENDPOINTS.md`.

## Utils
- `app/utils/field_validators.py`: Field validation + hints.
- `app/utils/document_generator.py`: PDF/DOCX generation & HTML preview, signature embedding.
- `app/utils/pii_protector.py`: PII masking helpers.
- `app/services/document_agent.py`: Agent flow, CSV processing, encryption/hashing.

## Data Privacy
- Names encrypted with Fernet derived from `SECRET_KEY`.
- Phone/email hashed (SHA-256) for search.
- Previews mask PII before storage/display.

## Development Notes
- On startup, lightweight schema checks add missing columns (e.g., `email_hash`).
- CORS: Allowed localhost ports (3000/5173/6173 etc.) and permissive regex in dev.
- Logs: `/tmp/backend.log` via `dev-server.sh`.
# HR Letter Templates

Place your .docx template files in this directory.

## Template Naming Convention:

- `offer_letter.docx` - Offer Letter
- `experience_letter.docx` - Experience Letter  
- `relieving_letter.docx` - Relieving Letter
- `appointment_letter.docx` - Appointment Letter
- `promotion_letter.docx` - Promotion Letter
- `salary_increment_letter.docx` - Salary Increment Letter
- `confirmation_letter.docx` - Confirmation Letter
- `transfer_letter.docx` - Transfer Letter
- `warning_letter.docx` - Warning Letter
- `internship_offer_letter.docx` - Internship Offer Letter

## Placeholder Format:

Use `{{field_name}}` in your .docx templates for dynamic fields.

Example:
```
Dear {{employee_name}},

We are pleased to offer you the position of {{position}} at DHL Express.

Your joining date is {{join_date}}.
Your annual salary will be {{salary}}.

...
```

The system will automatically replace these placeholders with CSV data.
