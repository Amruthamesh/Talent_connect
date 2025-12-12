# API Endpoints Documentation
**For Frontend Integration - Backend v1.0**

**Base URL:** 
- Backend: `http://127.0.0.1:8000/api/v1`
- Frontend: `http://127.0.0.1:6173`

**Environment Variable:** Set `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1` in frontend `.env`

**Authentication:** All endpoints (except `/auth/login` and `/auth/demo-login`) require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

**CORS Configuration:** Backend allows origins:
- `http://localhost:6173`
- `http://127.0.0.1:6173`
- `http://localhost:8000`
- `http://127.0.0.1:8000`

---

## 📱 Frontend Routes

### Documents Module
- `/documents` - Documents dashboard (choose agent, library, or templates)
- `/documents/agent` - AI Document Agent (conversational generation)
- `/documents/query` - Document Library (search, view, download generated documents)
- `/documents/templates` - Template Manager (manage HR letter templates)

### Jobs Module
- `/jobs/generator` - Job Creation Choice
- `/jobs/create/chat` - Job Chat Builder
- `/jobs/create/form` - Job Form Review
- `/jobs/matcher` - Profile Matcher

### Interviews Module
- `/interviews/dashboard` - Interview Dashboard
- `/interviews/schedule` - Schedule Interview
- `/interviews/join/:interviewId` - Join Interview

---

## 🔐 Authentication Endpoints

### 1. Login
**POST** `/auth/login`

Login with email and password to get JWT token.

**Request:**
```json
{
  "username": "user@company.com",
  "password": "password123"
}
```

**Demo Accounts:**
- HR: `hr@talent.com` / `hrpass123`
- Admin: `admin@talent.com` / `adminpass123`

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@company.com",
    "full_name": "John Doe",
    "role": "hr",
    "is_active": true
  }
}
```

**Errors:**
- `401 Unauthorized` - Incorrect email or password
- `400 Bad Request` - Inactive user account

---

### 2. Demo Login
**POST** `/auth/demo-login`

Quick login with demo account (requires `ENABLE_DEMO_ACCOUNTS=true`).

**Request:**
```json
{
  "email": "demo@company.com"
}
```

**Response (200 OK):**
Same as Login endpoint

**Errors:**
- `403 Forbidden` - Demo accounts are disabled
- `404 Not Found` - Demo account not found

---

## 📄 Documents Endpoints

### 1. List Document Templates
**GET** `/documents/templates`

Get available document templates based on user role.

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Offer Letter",
    "category": "Employment",
    "description": "Standard offer letter template"
  },
  {
    "id": 2,
    "name": "Contract",
    "category": "Employment",
    "description": "Employment contract template"
  }
]
```

**Permissions:** `documents.view` (Implicit - all authenticated users)

---

### 2. Document Agent - Conversational Workflow

The document generation system uses a conversational AI agent that guides users through template selection, data input, preview, and final generation with PII protection.

#### 2.1 Start Conversation
**POST** `/documents/agent/start`

Initialize a new document generation session.

**Request:** `{}`

**Response (200 OK):**
```json
{
  "session_id": "uuid-session-id",
  "message": "Hello! I'm here to help you generate HR documents. What would you like to create today?",
  "options": [
    {"id": 1, "name": "Offer Letter"},
    {"id": 2, "name": "Employment Contract"},
    {"id": 3, "name": "Appointment Letter"}
  ]
}
```

#### 2.2 Select Template
**POST** `/documents/agent/select-template`

Choose which document template to use.

**Request:**
```json
{
  "session_id": "uuid-session-id",
  "template_id": 1
}
```

**Response (200 OK):**
```json
{
  "message": "Great! You've selected Offer Letter. How would you like to provide the data?",
  "options": ["Manual Entry", "Upload CSV", "Download Template"]
}
```

#### 2.3 Choose Input Method
**POST** `/documents/agent/input-method`

Select data entry approach.

**Request:**
```json
{
  "session_id": "uuid-session-id",
  "method": "upload_csv"
}
```

**Options:** `manual_entry`, `upload_csv`, `download_template`

#### 2.4 Upload CSV Data
**POST** `/documents/agent/upload-csv`

Upload CSV file with recipient data for bulk generation.

**Request (multipart/form-data):**
```
file: <csv_file>
session_id: "uuid-session-id"
```

**CSV Format:**
```csv
Recipient Name,Employee Code,Designation,Department,Salary,Join Date,Signatory Name,Signatory Designation
John Doe,EMP001,Senior Engineer,Engineering,120000,2025-12-01,Jane Manager,VP Engineering
Jane Smith,EMP002,Product Manager,Product,110000,2025-12-15,Bob Director,Chief Product Officer
```

**Response (200 OK):**
```json
{
  "message": "CSV uploaded successfully! Found 2 records.",
  "next_step": "preview"
}
```

#### 2.5 Manual Field Entry
**POST** `/documents/agent/manual-field`

Enter individual field values manually.

**Request:**
```json
{
  "session_id": "uuid-session-id",
  "field_name": "Recipient Name",
  "field_value": "John Doe"
}
```

#### 2.6 Complete Manual Entry
**POST** `/documents/agent/manual-complete`

Signal completion of manual data entry.

**Request:**
```json
{
  "session_id": "uuid-session-id",
  "action": "generate"
}
```

**Actions:** `add_another` (add more recipients), `generate` (proceed to preview)

#### 2.7 Upload Signature
**POST** `/documents/agent/upload-signature`

Upload signature image for document signing.

**Request (multipart/form-data):**
```
file: <image_file>
session_id: "uuid-session-id"
```

**Supported formats:** PNG, JPG, JPEG

#### 2.8 Preview Document
**POST** `/documents/agent/preview`

Generate PII-masked preview HTML before final generation.

**Request:**
```json
{
  "session_id": "uuid-session-id"
}
```

**Response (200 OK):**
```json
{
  "preview_html": "<html><body>...[PII Protected] placeholders...</body></html>",
  "all_fields_valid": true,
  "missing_fields": []
}
```

#### 2.9 Generate Documents
**POST** `/documents/agent/generate`

Generate final documents with encryption and PII protection.

**Request:**
```json
{
  "session_id": "uuid-session-id",
  "format": "pdf"
}
```

**Response (200 OK):**
```json
{
  "generated_count": 2,
  "document_ids": [123, 124],
  "message": "Successfully generated 2 Offer Letter documents."
}
```

**Document Storage:**
- `recipient_name`: Encrypted with Fernet
- `phone_number`: SHA256 hash only
- `email`: SHA256 hash only
- `preview_masked_html`: PII-masked version for safe display
- `document_type`: Saved as proper name (e.g., "Offer Letter", not "offer_letter")

---

### 3. Get Document Details
**GET** `/documents/{document_id}`

Get details of a specific document.

**Response (200 OK):**
```json
{
  "id": 123,
  "name": "Offer Letter - John Doe",
  "created_at": "2025-11-15T10:00:00Z"
}
```

**Errors:**
- `404 Not Found` - Document not found

---

### 5. Query Documents
**GET** `/documents/query`

Search and retrieve generated documents with PII-protected previews.

**Query Parameters:**
- `recipient_name` (string, optional): Search by recipient name (partial match, case-insensitive) - **DEFAULT SEARCH**
- `employee_code` (string, optional): Search by employee code (exact match)
- `phone_number` (string, optional): Search by phone number hash
- `document_type` (string, optional): Filter by document type (e.g., "Offer Letter", "Contract")
- `limit` (int, optional): Max results (default: 20)

**Response (200 OK):**
```json
{
  "documents": [
    {
      "id": 123,
      "recipient_name": "John Doe",
      "employee_code": "EMP001",
      "document_type": "Offer Letter",
      "preview_masked_html": "<html>...PII masked preview...</html>",
      "generated_at": "2025-11-27T14:32:10Z"
    },
    {
      "id": 124,
      "recipient_name": "Jane Smith",
      "employee_code": "EMP002",
      "document_type": "Offer Letter",
      "preview_masked_html": "<html>...PII masked preview...</html>",
      "generated_at": "2025-11-27T15:10:45Z"
    }
  ],
  "total": 2
}
```

**PII Protection:**
- `recipient_name`: Encrypted in database, decrypted for display
- `phone_number`: SHA256 hash for search only
- `email`: SHA256 hash for search only
- `preview_masked_html`: PII fields masked with `[PII Protected]` placeholders

**Example Searches:**
- By recipient name: `/documents/query?recipient_name=john`
- By employee code: `/documents/query?employee_code=EMP001`
- By document type: `/documents/query?document_type=Offer%20Letter`
- Combined: `/documents/query?recipient_name=smith&document_type=Contract&limit=10`

**Permissions:** `documents.view` (HR/Admin only)

---

### 6. Download Document
**GET** `/documents/{document_id}/download`

Download generated document with actual data filled (not placeholders).

**Query Parameters:**
- `format` (string, optional): File format - `pdf` (default) or `docx`

**Response (200 OK):**
- **Content-Type:** `application/pdf` or `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Content-Disposition:** `attachment; filename="{recipient_name}_{date}_{document_type}.{ext}"`

**Filename Format:**
- Pattern: `{recipient_name}_{YYYYMMDD}_{document_type}.{ext}`
- Example: `John_Doe_20251127_Offer_Letter.pdf`
- Example: `Jane_Smith_20251127_Contract.docx`

**Document Generation:**
- Uses `DocumentGenerator` to fill template with actual encrypted data
- All placeholders replaced with real values (name, salary, dates, signatures, etc.)
- Signatures injected as HTML if available

**Example Request:**
```
GET /api/v1/documents/123/download?format=pdf
Authorization: Bearer <token>
```

**Errors:**
- `404 Not Found` - Document not found
- `500 Internal Server Error` - Template file missing or generation failed

**Permissions:** `documents.view`

---

### 7. Complete Document Generation Workflow

#### Example: Generate Offer Letters via CSV Upload

**Step 1: Start Session**
```javascript
const startResponse = await fetch('/api/v1/documents/agent/start', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({})
});
const { session_id } = await startResponse.json();
```

**Step 2: Select Template**
```javascript
await fetch('/api/v1/documents/agent/select-template', {
  method: 'POST',
  headers: { 'Authorization': 'Bearer <token>', 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: session_id,
    template_id: 1  // Offer Letter
  })
});
```

**Step 3: Choose CSV Upload**
```javascript
await fetch('/api/v1/documents/agent/input-method', {
  method: 'POST',
  headers: { 'Authorization': 'Bearer <token>', 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: session_id,
    method: 'upload_csv'
  })
});
```

**Step 4: Upload CSV File**
```javascript
const formData = new FormData();
formData.append('file', csvFile);
formData.append('session_id', session_id);

await fetch('/api/v1/documents/agent/upload-csv', {
  method: 'POST',
  headers: { 'Authorization': 'Bearer <token>' },
  body: formData
});
```

**Step 5: Preview Documents**
```javascript
const previewResponse = await fetch('/api/v1/documents/agent/preview', {
  method: 'POST',
  headers: { 'Authorization': 'Bearer <token>', 'Content-Type': 'application/json' },
  body: JSON.stringify({ session_id: session_id })
});
const { preview_html } = await previewResponse.json();
// Display preview_html in modal
```

**Step 6: Generate Final Documents**
```javascript
const generateResponse = await fetch('/api/v1/documents/agent/generate', {
  method: 'POST',
  headers: { 'Authorization': 'Bearer <token>', 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: session_id,
    format: 'pdf'
  })
});
const { document_ids } = await generateResponse.json();
// Navigate to /documents/query
```

**Step 7: Search Generated Documents**
```javascript
const queryResponse = await fetch(
  '/api/v1/documents/query?recipient_name=john',
  {
    headers: { 'Authorization': 'Bearer <token>' }
  }
);
const { documents } = await queryResponse.json();
// Display documents in library
```

**Step 8: Download Document**
```javascript
const downloadUrl = `/api/v1/documents/${documentId}/download?format=pdf`;
window.open(downloadUrl);
// Downloads as: John_Doe_20251127_Offer_Letter.pdf
```

---

## 📋 Interviews Endpoints

### 1. List Interviews
**GET** `/interviews`

Get all interviews for the current user.

**Query Parameters:**
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Number of records to return (default: 10)

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "candidate_name": "Jane Smith",
    "candidate_email": "jane@example.com",
    "role": "Product Manager",
    "company": "Tech Corp",
    "round_type": "technical",
    "scheduled_at": "2025-11-25T14:00:00Z",
    "status": "scheduled",
    "interviewer_key": "key123",
    "candidate_key": "key456",
    "notes": "Check leadership experience",
    "transcript": [],
    "feedback": null
  }
]
```

**Permissions:** `interviews.dashboard`

---

### 2. Schedule Interview
**POST** `/interviews/schedule`

Schedule a new interview with optional file uploads.

**Request (multipart/form-data):**
```
candidate_name: "Jane Smith" (required)
candidate_email: "jane@example.com" (optional)
role: "Product Manager" (required)
company: "Tech Corp" (optional)
round_type: "technical" (required) - one of: phone_screen, technical, design, system_design, behavioral, final
date: "2025-11-25" (required)
time: "14:00" (required)
notes: "Check leadership experience" (optional)
jd_text: "Job description text..." (optional)
resume: <file> (optional)
job_description: <file> (optional)
```

**Response (201 Created):**
```json
{
  "id": 1,
  "candidate_name": "Jane Smith",
  "candidate_email": "jane@example.com",
  "role": "Product Manager",
  "company": "Tech Corp",
  "round_type": "technical",
  "scheduled_at": "2025-11-25T14:00:00Z",
  "status": "scheduled",
  "interviewer_key": "key123",
  "candidate_key": "key456",
  "notes": "Check leadership experience",
  "transcript": [],
  "feedback": null
}
```

**Permissions:** `interviews.schedule`

---

### 3. Get Interview Details
**GET** `/interviews/{interview_id}`

Get details of a specific interview.

**Response (200 OK):** Same as List Interviews response (single object)

**Errors:**
- `404 Not Found` - Interview not found

---

### 4. Update Interview Status
**PUT** `/interviews/{interview_id}/status`

Update interview status (scheduled, in_progress, completed, cancelled).

**Query Parameters:**
- `key` (string, required): Interviewer key for authorization

**Request:**
```json
{
  "status": "completed"
}
```

**Response (200 OK):** Updated interview object

**Errors:**
- `404 Not Found` - Interview not found
- `403 Forbidden` - Invalid interviewer key

---

### 5. Send Question to Candidate
**POST** `/interviews/{interview_id}/questions`

Send a question during the interview.

**Query Parameters:**
- `key` (string, required): Interviewer key for authorization

**Request:**
```json
{
  "question": "Tell me about your most challenging project"
}
```

**Response (200 OK):** Updated interview object with new question

**Errors:**
- `404 Not Found` - Interview not found
- `403 Forbidden` - Invalid interviewer key

---

### 6. Submit Candidate Response
**POST** `/interviews/{interview_id}/responses`

Submit a response to a question.

**Query Parameters:**
- `key` (string, required): Candidate key for authorization

**Request:**
```json
{
  "question_id": 1,
  "answer": "I led a team to rebuild our authentication system..."
}
```

**Response (200 OK):** Updated interview object with new response

**Errors:**
- `404 Not Found` - Interview not found
- `403 Forbidden` - Invalid candidate key

---

### 7. Submit Interview Feedback
**POST** `/interviews/{interview_id}/feedback`

Submit feedback after interview completion.

**Query Parameters:**
- `key` (string, required): Interviewer key for authorization

**Request:**
```json
{
  "technical_score": 8,
  "communication_score": 7,
  "cultural_fit_score": 8,
  "overall_assessment": "Strong candidate with solid technical skills",
  "recommendation": "hire"
}
```

**Response (200 OK):** Updated interview object with feedback

**Errors:**
- `404 Not Found` - Interview not found
- `403 Forbidden` - Invalid interviewer key

---

### 8. Resolve Interview by Key
**GET** `/interviews/resolve/key`

Resolve a join key to get interview details and user role.

**Query Parameters:**
- `key` (string, required): Interview access key

**Response (200 OK):**
```json
{
  "role": "interviewer",
  "interview": { /* interview object */ }
}
```

**Notes:** Used for lobby/session access where you have a key but no auth token.

**Errors:**
- `404 Not Found` - Invalid key

---

### 9. WebSocket Connection (Real-time Interview)
**WS** `/interviews/{interview_id}/ws`

Connect via WebSocket for real-time interview communication.

**Query Parameters:**
- `key` (string, required): Interview access key (interviewer or candidate)

**Connection Flow:**

1. **Connect:**
   - Receive: `{"type": "connected", "role": "interviewer|candidate"}`

2. **Interviewer sends question:**
   - Send: `{"type": "question", "question": "Tell me about yourself"}`
   - Broadcast: `{"type": "question", "interview_id": 1, "question": {...}}`

3. **Candidate sends response:**
   - Send: `{"type": "response", "question_id": 1, "answer": "I am..."}`
   - Broadcast: `{"type": "response", "interview_id": 1, "question_id": 1, "answer": "I am..."}`

4. **Interviewer updates status:**
   - Send: `{"type": "status", "status": "completed"}`
   - Broadcast: `{"type": "status", "interview_id": 1, "status": "completed"}`

**Example (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/interviews/1/ws?key=key123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'connected') {
    console.log('Connected as', data.role);
  } else if (data.type === 'question') {
    console.log('New question:', data.question);
  }
};

// Send a question (if interviewer)
ws.send(JSON.stringify({
  type: 'question',
  question: 'What is your experience with React?'
}));
```

---

## 💼 Jobs Endpoints

### 1. Generate Job Description
**POST** `/jobs/generate-jd`

Generate comprehensive job description with AI.

**Request:**
```json
{
  "role": "Senior Software Engineer",
  "seniority": "senior",
  "expectations": "Lead technical initiatives and mentor junior engineers",
  "must_have_skills": ["Python", "React", "System Design"],
  "preferred_skills": ["AWS", "Docker", "Kubernetes"],
  "company_tone": "professional",
  "department": "Engineering",
  "location": "Remote"
}
```

**Response (200 OK):**
```json
{
  "content": "# Senior Software Engineer...",
  "role": "Senior Software Engineer",
  "generated_at": "2025-11-24T10:30:00Z",
  "metadata": {
    "skill_matrix": [
      {"skill": "Python", "proficiency": "expert", "importance": "critical"},
      {"skill": "React", "proficiency": "advanced", "importance": "critical"}
    ],
    "salary_benchmark": "$150,000 - $200,000",
    "insights": "High demand for this role in current market"
  }
}
```

**Permissions:** `jobs.generate_jd`

---

### 2. Explain JD to Candidate
**POST** `/jobs/explain-jd`

Translate technical JD into candidate-friendly explanation.

**Request:**
```json
{
  "jd_content": "# Senior Software Engineer...",
  "role": "Senior Software Engineer"
}
```

**Response (200 OK):**
```json
{
  "explanation": "Are you an experienced engineer looking to take on leadership... ",
  "role": "Senior Software Engineer"
}
```

**Permissions:** `jobs.generate_jd`

---

### 3. Rewrite JD for Manager
**POST** `/jobs/rewrite-jd`

Rewrite JD as internal hiring manager briefing.

**Request:**
```json
{
  "jd_content": "# Senior Software Engineer...",
  "role": "Senior Software Engineer"
}
```

**Response (200 OK):**
```json
{
  "manager_briefing": "## Hiring Brief for Senior Software Engineer\n\nKey Interview Topics:\n- System Design experience...",
  "role": "Senior Software Engineer"
}
```

**Permissions:** `jobs.generate_jd`

---

### 4. Skill Autocomplete
**GET** `/jobs/skills/autocomplete`

Autocomplete skill suggestions as user types.

**Query Parameters:**
- `query` (string, required): Search query
- `category` (string, optional): Skill category filter
- `limit` (int, optional): Max results (default: 10)

**Response (200 OK):**
```json
{
  "suggestions": [
    {
      "name": "Python",
      "category": "Programming Language",
      "popularity_score": 0.95
    },
    {
      "name": "PyTorch",
      "category": "ML Framework",
      "popularity_score": 0.87
    }
  ]
}
```

---

### 5. Job Builder Chat (Interactive)
**POST** `/jobs/chat-builder`

Interactive chat to build job description step-by-step.

**Request:**
```json
{
  "message": "I need a job description for a Product Manager role"
}
```

**Response (200 OK):**
```json
{
  "response": "Great! I'll help you create a Product Manager job description...",
  "next_questions": [
    "What level of seniority are you hiring for?",
    "What's the team size they'll manage?"
  ],
  "draft_jd": null
}
```

---

## 🎯 Profile Matcher Endpoints

### 1. Upload Resumes & Stream Evaluation
**POST** `/matcher/upload`

Upload multiple resumes and stream AI evaluation results via Server-Sent Events (SSE).

**Request (multipart/form-data):**
```
job_description: "Senior Python developer with 5+ years..." (required)
files: [resume1.pdf, resume2.pdf, ...] (required, at least 1 file)
```

**Response (200 OK - SSE Stream):**

Sends events as each resume is evaluated:
```
event: update
data: {"file":"resume1.pdf","candidate_name":"John Smith","match_score":0.92,"key_matches":["Python","AWS"],"missing_skills":["Kubernetes"],"summary":"Strong match...","upload_id":1}

event: update
data: {"file":"resume2.pdf","candidate_name":"Jane Doe","match_score":0.78,...,"upload_id":2}

event: done
data: {}
```

**Permissions:** `jobs.matcher.use`

**Frontend Integration (JavaScript):**
```javascript
const formData = new FormData();
formData.append('job_description', jobDesc);
formData.append('files', file1);
formData.append('files', file2);

const eventSource = new EventSource('/api/v1/matcher/upload', {
  method: 'POST',
  body: formData
});

eventSource.addEventListener('update', (event) => {
  const result = JSON.parse(event.data);
  console.log(`Evaluated: ${result.file} - Score: ${result.match_score}`);
});

eventSource.addEventListener('error', (event) => {
  const error = JSON.parse(event.data);
  console.error(`Error: ${error.file} - ${error.message}`);
});

eventSource.addEventListener('done', () => {
  console.log('All resumes evaluated');
  eventSource.close();
});
```

---

### 2. Get Candidate Profile
**GET** `/matcher/candidate/{candidate_id}`

Retrieve parsed candidate profile with extracted information.

**Response (200 OK):**
```json
{
  "id": 1,
  "full_name": "John Smith",
  "email": "john@example.com",
  "phone": "+1-555-0123",
  "summary": "Senior Software Engineer with 8+ years experience...",
  "skills": ["Python", "Java", "AWS", "Docker"],
  "experiences": [
    {
      "company": "Tech Corp",
      "position": "Senior Engineer",
      "duration": "2021-Present",
      "description": "Led team of 5 engineers..."
    }
  ],
  "education": [
    {
      "school": "MIT",
      "degree": "BS Computer Science",
      "year": "2016"
    }
  ],
  "raw_text": "Full resume text...",
  "uploaded_at": "2025-11-24T10:00:00Z"
}
```

**Errors:**
- `404 Not Found` - Candidate not found

---

### 3. Download Selected Resumes
**POST** `/matcher/download-zip`

Download selected resumes as a ZIP file.

**Request:**
```json
{
  "candidate_ids": [1, 2, 3]
}
```

**Response:** ZIP file download

**Permissions:** `jobs.matcher.use`

---

## 📊 Response Models & Schemas

### User Model
```json
{
  "id": 1,
  "email": "user@company.com",
  "full_name": "John Doe",
  "role": "hr",
  "is_active": true,
  "created_at": "2025-01-15T10:00:00Z"
}
```

### Interview Model
```json
{
  "id": 1,
  "candidate_name": "Jane Smith",
  "candidate_email": "jane@example.com",
  "role": "Product Manager",
  "company": "Tech Corp",
  "round_type": "technical",
  "scheduled_at": "2025-11-25T14:00:00Z",
  "status": "scheduled",
  "interviewer_key": "abc123",
  "candidate_key": "xyz789",
  "notes": "Check leadership experience",
  "transcript": [
    {"type": "question", "text": "Tell me about yourself", "timestamp": "2025-11-25T14:00:30Z"},
    {"type": "response", "text": "I have 10 years of experience...", "timestamp": "2025-11-25T14:01:00Z"}
  ],
  "feedback": {
    "technical_score": 8,
    "communication_score": 7,
    "cultural_fit_score": 9,
    "overall_assessment": "Strong candidate",
    "recommendation": "hire"
  },
  "created_at": "2025-11-24T10:00:00Z"
}
```

---

## 🔑 Permission Matrix

| Resource | Permission | Roles |
|----------|-----------|-------|
| Interviews | `interviews.dashboard` | HR, Interviewer |
| Interviews | `interviews.schedule` | HR |
| Documents | `documents.view` | All |
| Documents | `docs.query.full` | HR |
| Jobs | `jobs.generate_jd` | HR, Hiring Manager |
| Matcher | `jobs.matcher.use` | HR, Hiring Manager |

---

## 🔒 PII Protection & Security

The Talent Connect system implements comprehensive PII (Personally Identifiable Information) protection for all generated documents.

### Encryption & Hashing Strategy

**Encrypted Fields (Fernet):**
- `recipient_name`: Encrypted in database, decrypted only for authorized display/download
- Encryption key stored in environment variables (`ENCRYPTION_KEY`)

**Hashed Fields (SHA256):**
- `phone_number`: One-way hash for searchability without storing plaintext
- `email`: One-way hash for searchability without storing plaintext

**Masked Preview:**
- `preview_masked_html`: All PII replaced with `[PII Protected]` placeholders
- Safe to display without decryption
- Used in document query results

### Data Flow

1. **Document Generation:**
   - User provides CSV/manual data
   - System generates PDF/DOCX with actual values
   - Stores encrypted recipient name
   - Creates SHA256 hashes for phone/email
   - Generates masked HTML preview

2. **Document Query:**
   - Returns `preview_masked_html` with PII masked
   - Decrypts `recipient_name` for display only
   - No exposure of phone/email plaintext

3. **Document Download:**
   - Decrypts stored data
   - Regenerates PDF/DOCX with actual values
   - Serves file with sanitized filename

### Search Capabilities

**Searchable by:**
- Recipient name (partial match via decrypted values)
- Employee code (exact match, stored plaintext)
- Phone number (hash comparison)
- Email (hash comparison)
- Document type (plaintext category)

**Example:**
```
GET /api/v1/documents/query?recipient_name=john
GET /api/v1/documents/query?employee_code=EMP001
GET /api/v1/documents/query?phone_number=+1-555-0123
```

### Security Best Practices

- Never log decrypted PII
- Encryption key must be 32 URL-safe base64-encoded bytes
- Rotate encryption keys periodically (requires data re-encryption)
- Use HTTPS in production
- Limit document access to HR/Admin roles only

---

## ⚠️ Common Errors

### 400 Bad Request
```json
{
  "detail": "Invalid request data"
}
```
**Causes:**
- Missing required fields in request body
- Invalid CSV format (missing columns, wrong headers)
- Invalid file format (non-PDF template, non-image signature)

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```
**Causes:**
- Missing `Authorization` header
- Invalid or expired JWT token
- Token not in format `Bearer <token>`

**Fix:**
```javascript
// Ensure token is stored and sent correctly
const token = localStorage.getItem('user');
const user = JSON.parse(token);
headers['Authorization'] = `Bearer ${user.access_token}`;
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```
**Causes:**
- User role lacks required permission
- Trying to access documents without `documents.view` permission
- Trying to generate JD without `jobs.generate_jd` permission

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```
**Document-specific causes:**
- Document ID doesn't exist
- Template file path incorrect in database
- Template PDF file missing from filesystem

**Check:**
```sql
SELECT id, name, file_path FROM document_templates;
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```
**Document-specific causes:**
- Encryption key not set (`ENCRYPTION_KEY` missing)
- Failed to decrypt data (`InvalidToken` exception)
- Template file corrupted or unreadable
- PDF generation failure (missing fonts, invalid data)

**Debug steps:**
1. Check backend logs for stack trace
2. Verify template file exists at `file_path`
3. Ensure `ENCRYPTION_KEY` is set in environment
4. Test decryption with known encrypted value

---

## 🚀 Quick Start for Frontend

### 1. Login & Authentication
```javascript
// Login
const response = await fetch('http://127.0.0.1:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    username: 'hr@talent.com',
    password: 'hrpass123'
  })
});
const data = await response.json();

// Store entire user object (includes token)
localStorage.setItem('user', JSON.stringify(data));
```

### 2. Make Authenticated Requests
```javascript
// Retrieve stored user data
const user = JSON.parse(localStorage.getItem('user'));

const headers = {
  'Authorization': `Bearer ${user.access_token}`,
  'Content-Type': 'application/json'
};

// Example: Get documents
const response = await fetch('http://127.0.0.1:8000/api/v1/documents/query?recipient_name=john', {
  headers
});
```

### 3. Generate Documents via Agent
```javascript
// Start session
let sessionId;
const startResp = await fetch('http://127.0.0.1:8000/api/v1/documents/agent/start', {
  method: 'POST',
  headers
});
sessionId = (await startResp.json()).session_id;

// Select template
await fetch('http://127.0.0.1:8000/api/v1/documents/agent/select-template', {
  method: 'POST',
  headers,
  body: JSON.stringify({ session_id: sessionId, template_id: 1 })
});

// Upload CSV
const formData = new FormData();
formData.append('file', csvFile);
formData.append('session_id', sessionId);

await fetch('http://127.0.0.1:8000/api/v1/documents/agent/upload-csv', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${user.access_token}` },
  body: formData
});

// Generate
const genResp = await fetch('http://127.0.0.1:8000/api/v1/documents/agent/generate', {
  method: 'POST',
  headers,
  body: JSON.stringify({ session_id: sessionId, format: 'pdf' })
});
const { document_ids } = await genResp.json();
```

### 4. Download Document
```javascript
// Download PDF
const downloadUrl = `http://127.0.0.1:8000/api/v1/documents/${documentId}/download?format=pdf`;
const link = document.createElement('a');
link.href = downloadUrl;
link.download = ''; // Browser will use Content-Disposition filename
link.click();

// Result: John_Doe_20251127_Offer_Letter.pdf
```

### 5. Upload Resumes with Progress (SSE)
```javascript
const formData = new FormData();
formData.append('job_description', jobDesc);
Array.from(files).forEach(f => formData.append('files', f));

const eventSource = new EventSource('http://127.0.0.1:8000/api/v1/matcher/upload', {
  method: 'POST',
  body: formData,
  headers: { 'Authorization': `Bearer ${user.access_token}` }
});

eventSource.addEventListener('update', (event) => {
  const result = JSON.parse(event.data);
  console.log(`Match Score: ${result.match_score}`);
});

eventSource.addEventListener('done', () => {
  eventSource.close();
});
```

---

## 📞 Support & Questions

For issues or questions about API integration:
1. Check the endpoint documentation above
2. Verify authentication token is valid and in correct format
3. Ensure request format matches the schema
4. Use **http://127.0.0.1:8000** (not localhost) to match CORS config
5. Check backend logs for detailed error messages
6. Verify `.env` has `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1`

**Common Pitfalls:**
- ❌ Using `http://localhost:8000` instead of `http://127.0.0.1:8000` (CORS error)
- ❌ Storing only `access_token` instead of full user object
- ❌ Forgetting `Bearer ` prefix in Authorization header
- ❌ Not handling hard refresh after `.env` changes (Ctrl+Shift+R)

