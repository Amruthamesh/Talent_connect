# API Endpoints Documentation
**For Frontend Integration - Backend v1.0**

**Base URL:** `http://localhost:8000/api/v1`

**Authentication:** All endpoints (except `/auth/login` and `/auth/demo-login`) require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

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

### 2. Agent Conversation Flow
The frontend uses an agentic flow for templates, data entry, preview and generation:

1) **POST** `/documents/agent/start`
  - Starts a session → `{ session_id, message, options }`
2) **POST** `/documents/agent/select-template`
  - `{ session_id, template_id }`
3) **POST** `/documents/agent/input-method`
  - `{ session_id, method }` // `manual_entry | upload_csv | download_template`
4) **POST** `/documents/agent/manual-field`
  - `{ session_id, field_name, field_value }`
5) **POST** `/documents/agent/manual-complete`
  - `{ session_id, action }` // `add_another | generate`
6) **POST** `/documents/agent/preview`
  - `{ session_id }` → `{ preview_html, all_fields_valid }`
7) **POST** `/documents/agent/generate`
  - `{ session_id, format }` → `{ generated_count, document_ids }`
8) **POST** `/documents/agent/upload-csv`
  - FormData: `file`, `session_id`
9) **POST** `/documents/agent/upload-signature`
  - FormData: `file`, `session_id`

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

Search generated documents via filters.

**Query params:**
- `employee_code`
- `phone_number`
- `document_type`
- `limit` (default 20)

**Response (200 OK):**
```json
{
  "documents": [
    {
      "id": 123,
      "document_type": "offer_letter",
      "preview_masked_html": "...masked...",
      "generated_at": "2025-11-27T00:01:24Z"
    }
  ],
  "total": 1
}
```
**Permissions:** HR/admin
      "name": "Offer Letter - John Doe",
      "relevance_score": 0.95
    }
  ],
  "total": 1,
  "query": "offer letters for engineers"
}
```

**Permissions:** `docs.query.full` (HR only)

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

## ⚠️ Common Errors

### 400 Bad Request
```json
{
  "detail": "Invalid request data"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## 🚀 Quick Start for Frontend

### 1. Login
```javascript
const response = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    username: 'user@company.com',
    password: 'password123'
  })
});
const { access_token } = await response.json();
localStorage.setItem('token', access_token);
```

### 2. Make Authenticated Requests
```javascript
const headers = {
  'Authorization': `Bearer ${localStorage.getItem('token')}`,
  'Content-Type': 'application/json'
};

// Example: Get interviews
const response = await fetch('http://localhost:8000/api/v1/interviews', {
  headers
});
```

### 3. Upload Resumes with Progress
```javascript
const formData = new FormData();
formData.append('job_description', jobDesc);
Array.from(files).forEach(f => formData.append('files', f));

const eventSource = new EventSource('/api/v1/matcher/upload', {
  method: 'POST',
  body: formData,
  headers: { 'Authorization': `Bearer ${token}` }
});

eventSource.addEventListener('update', handleUpdate);
eventSource.addEventListener('done', handleDone);
```

---

## 📞 Support & Questions

For issues or questions about API integration:
1. Check the endpoint documentation above
2. Verify authentication token is valid
3. Ensure request format matches the schema
4. Check backend logs for detailed error messages

