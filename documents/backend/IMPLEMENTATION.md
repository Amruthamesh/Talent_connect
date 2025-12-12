# Talent Connect Backend — Implementation Guide

This document explains how the backend is wired end-to-end, the major modules, and how the profile matcher outperforms a traditional ATS.

## Stack and Entry Points
- **Framework:** FastAPI (async) with Pydantic models and SQLAlchemy async ORM.
- **App entry:** `app/main.py` creates the FastAPI app, sets CORS, auto-creates tables on startup, and mounts the v1 API router under `settings.API_V1_STR` (default `/api/v1`).
- **Configuration:** `app/config.py` via `pydantic-settings` (env file `.env`). Controls DB URL, CORS, JWT secret/expiry, upload dir, debug, and AI keys.

## Modules and Data Flow
### Authentication & RBAC
- **JWT issuance/verification:** `app/core/auth.py` issues tokens with `sub=email`, bcrypt-based password hashing, and guards via `get_current_active_user`.
- **Permissions:** `app/core/permissions.py` maps permission strings to roles and provides `require_permission`/`require_roles` dependencies for routers. Permission matrix aligns with frontend.

### Database Layer
- **Engine/Session:** `app/db/session.py` defines async engine and session factory; `get_db` yields a transactional `AsyncSession`.
- **Metadata hook:** `app/db/base.py` imports all models so `create_all` sees them.
- **Seeder:** `app/db/init_db.py` creates tables and seeds demo HR/manager/recruiter users with hashed passwords.

### Models (SQLAlchemy)
- **Users:** `users` table (`app/models/user.py`) with role (`hr`, `hiring_manager`, `recruiter`), active flag, and timestamps.
- **Matcher:** `app/models/matcher.py` holds:
  - `jobs` (title/description/skills),
  - `resume_uploads` (file metadata/status),
  - `candidate_profiles` (parsed resume data + JSON blobs),
  - `match_runs` and `match_results` (scores, matched/missing skills, rationales).
- **JD Uploads:** `app/models/jd_upload.py` stores uploaded JDs and extracted text.
- **Interviews:** `app/models/interview.py` stores scheduling fields, unique join keys for interviewer/candidate, transcript JSON, and feedback.

### API Routers (v1)
- **Auth (`app/api/v1/auth.py`):** Login (OAuth2 form), demo-login toggle, `/me`, and logout stub. Issues JWTs with configured expiry.
- **Jobs (`app/api/v1/jobs.py`):** AI JD generation/explain/rewrite via `JDGeneratorAgent`; skills autocomplete/categories; interactive chat builder for job forms via `JobBuilderChatAgent`; placeholder job listing; mock match-profiles endpoint.
- **Documents (`app/api/v1/documents.py`):** Stubbed templates list (role-filtered), generate, query, and download endpoints with TODOs for AI/RAG.
- **Profile Matcher (`app/api/v1/matcher.py`):** 
  - `POST /matcher/upload`: multipart uploads + JD text; streams AI evaluation per file via Server-Sent Events (SSE).
  - `GET /matcher/candidate/{id}`: returns parsed profile.
  - `POST /matcher/download-zip`: bundles selected resumes into a ZIP.
  - All gated by `jobs.matcher.use`.
- **Interviews (`app/api/v1/interviews.py`):** Schedule (form-data with optional resume/JD files), list/get, status updates (key-guarded), add questions/responses/feedback, resolve by join key, and a WebSocket endpoint for live Q&A/status broadcast via `ws_manager`.

### Services & Utilities
- **AI JD Generation:** `app/services/ai/jd_generator.py` uses OpenAI (GPT-4o-mini) to produce structured JD content (skill matrix, salary benchmark, insights). Requires `OPENAI_API_KEY`.
- **Chat Job Builder:** `app/services/ai/job_builder_chat.py` is a conversational agent that extracts required job fields, tracks completion, and can suggest defaults when users say “you decide.”
- **Profile Matcher Pipeline:** `app/services/ai/profile_matcher.py`
  - Saves uploaded bytes to disk (under `settings.UPLOAD_DIR`),
  - Parses resume via `app/utils/resume_parser.py` (PDF/DOCX/text) extracting name/email/phone/skills/experience summary,
  - Calls OpenAI with JD + parsed profile to return JSON: match %, strengths/gaps, recommendations, follow-up questions,
  - Merges AI result with parsed metadata and stored path.
- **Skills Autocomplete:** `app/services/skills_database.py` (in-memory skill catalog) powers `/jobs/skills/autocomplete` and `/jobs/skills/categories`.
- **Interview Service:** `app/services/interview_service.py` encapsulates CRUD, transcript updates, feedback, and key generation; `app/services/ws_manager.py` manages websocket connections per interview.
- **Storage Helpers:** `app/utils/storage.py` saves UploadFile objects with UUIDs; `app/utils/resume_parser.py` provides lightweight text/email/phone/skill extraction heuristics.

## Request Lifecycles (Key Flows)
- **Login:** `/auth/login` → validates user (DB) → bcrypt check → issues JWT with expiry.
- **JD Generation:** `/jobs/generate-jd` → permission `jobs.generate_jd` → OpenAI call → structured JD response (content + skill matrix + salary + insights).
- **Chat Job Builder:** `/jobs/chat/interactive-builder` → feeds history + current extracted data to AI → merges responses and returns completion % + optional summary.
- **Profile Matcher Upload:** `/matcher/upload` → permission `jobs.matcher.use` → reads files into memory → for each file: create `ResumeUpload` row, parse resume, AI evaluate vs JD, store path/status, stream SSE updates → `done` event.
- **Candidate Profile Fetch:** `/matcher/candidate/{id}` → joins upload to show parsed profile and upload timestamp.
- **Resume ZIP:** `/matcher/download-zip` → filters by upload ids → streams ZIP of stored files.
- **Interviews (WS):** `/interviews/{id}/ws?key=...` → key-auth → per-connection DB session → broadcast questions/responses/status to all participants in that interview room.

## Configuration & Operations
- **Env vars:** set in `.env` (SECRET_KEY, DB URL, AI keys, upload dir, CORS). See `app/config.py` defaults.
- **DB:** defaults to SQLite `sqlite+aiosqlite:///backend/talent_connect.db`; replace with Postgres URL for production.
- **Uploads:** stored under `uploads/` (configurable). SSE pipeline writes files to disk before parsing/evaluating.
- **Docs:** interactive docs at `/api/v1/docs` (Swagger) and `/api/v1/redoc`.

## Flex: Why the Profile Matcher Beats a Traditional ATS
- **Context-aware scoring:** Uses LLM reasoning to align skills, experience narratives, and gaps against the supplied JD—instead of simple keyword or Boolean matching typical in many ATS filters.
- **Richer signals from messy resumes:** Lightweight parsing handles PDF/DOCX/text, extracts contact info + heuristics for skills/experience, then lets the AI normalize/interpret noisy phrasing (e.g., synonyms, project descriptions) that keyword parsers miss.
- **Streaming feedback loop:** SSE returns per-file evaluations in real time as they’re processed, so recruiters see results immediately without waiting for a batch job.
- **Strengths, gaps, and follow-ups:** The AI returns rationale, matched/missing skills, and suggested follow-up questions—actionable guidance beyond a single score.
- **Human-in-the-loop ready:** Stored uploads + parsed profiles let recruiters download originals (ZIP) and review structured data side-by-side, enabling quick overrides when needed.
- **Optimization levers vs ATS:** Because it’s model-driven, improving recall/precision is a prompt/config change (or model upgrade) rather than re-indexing or complex rules tuning. Swapping in vector search over profiles or fine-tuned models can further boost match quality without reworking the pipeline.
- **Cost effectiveness:** Evaluations run on demand per resume with small, fast models (GPT-4o-mini by default), avoiding always-on indexing costs, proprietary ATS license fees, and complex infrastructure. You only pay for tokens processed, so bursty hiring cycles incur minimal idle cost.
