# Metadata Extraction - Visual Architecture & Flow

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TALENT CONNECT - PROFILE MATCHER              │
│                   WITH METADATA EXTRACTION SYSTEM                 │
└─────────────────────────────────────────────────────────────────┘

                        USER UPLOADS RESUME
                              │
                              ▼
                    ┌──────────────────────┐
                    │   Save File to Disk  │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                                 │
              ▼                                 ▼
    ┌─────────────────────┐         ┌──────────────────────┐
    │   Parse Resume      │         │ Extract Metadata     │
    │  (Text Extraction)  │         │  (MetadataExtractor) │
    └──────────┬──────────┘         └──────────┬───────────┘
               │                               │
               ├─ Name                        ├─ File Info
               ├─ Email                       ├─ Entities
               ├─ Phone                       │  ├─ Skills
               ├─ Skills (basic)              │  ├─ Emails
               └─ Experience Summary          │  ├─ Phones
                                              │  ├─ Degrees
                                              │  ├─ Locations
                                              │  └─ Dates
                                              ├─ Sections
                                              │  ├─ Experience
                                              │  ├─ Education
                                              │  ├─ Skills
                                              │  └─ ...
                                              └─ Quality Indicators
                                                 ├─ Is Scanned?
                                                 ├─ Text Length
                                                 └─ Section Count
              ┌────────────────┬────────────────┐
              │                │                │
              ▼                ▼                ▼
    ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │  PII Protection │  │  Quality Score   │  │  Combine Data    │
    │   (Apply Mask)  │  │  (MetadataAnalyzer)│ │                  │
    └────────┬────────┘  └────────┬─────────┘  └────────┬─────────┘
             │                    │                     │
             └────────────────────┼─────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │   LLM Evaluation        │
                    │ (evaluate_candidate)    │
                    │  - Candidate Skills     │
                    │  - Job Description      │
                    │  - Document Metadata    │
                    │  - Quality Indicators   │
                    └──────────┬──────────────┘
                               │
                               ▼
                    ┌──────────────────────────┐
                    │    Evaluation Results    │
                    │  - Match %               │
                    │  - Recommendation        │
                    │  - Document Quality      │
                    │  - Strengths/Gaps        │
                    └──────────┬───────────────┘
                               │
                               ▼
                    ┌──────────────────────────┐
                    │   Return to Client       │
                    │  (Streaming Response)    │
                    └──────────────────────────┘
```

## 🔄 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      INPUT: Resume File                      │
│                   (PDF, DOCX, TXT, etc.)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   ┌─────────┐        ┌──────────┐      ┌──────────┐
   │  PDF?   │        │  DOCX?   │      │  TXT?    │
   └────┬────┘        └────┬─────┘      └────┬─────┘
        │                  │                  │
        ▼                  ▼                  ▼
   ┌─────────────┐  ┌────────────────┐  ┌──────────┐
   │  PyPDF2     │  │  python-docx   │  │ read_text│
   │  Extract    │  │  Extract       │  │ Extract  │
   │  Text       │  │  Text          │  │ Text     │
   └─────┬───────┘  └────────┬───────┘  └────┬─────┘
         │                   │               │
         └───────────────────┼───────────────┘
                             │
                    ┌────────▼────────┐
                    │  Extracted Text │
                    │  (Raw Content)  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐         ┌──────────────┐     ┌─────────────┐
   │  Regex  │         │  Pattern     │     │  Heuristics │
   │  Email  │         │  Matching    │     │  Section    │
   │  Phone  │         │  Skills      │     │  Detection  │
   │  URL    │         │  Degrees     │     │             │
   │  Dates  │         │  Companies   │     │ Sections:   │
   │  Locs   │         │  Dates       │     │ • Exp       │
   └─────┬───┘         └────┬─────────┘     │ • Edu       │
         │                  │               │ • Skills    │
         └──────────────────┼───────────────┘ └────┬──────┘
                            │                      │
                  ┌─────────┴──────────┐           │
                  │                    │           │
                  ▼                    ▼           ▼
          ┌────────────────┐    ┌────────────────────┐
          │  Entities Dict │    │  Sections Dict     │
          │ {              │    │ {                  │
          │  emails: [...] │    │  experience: "..." │
          │  phones: [...] │    │  education: "..."  │
          │  skills: [...] │    │  skills: "..."     │
          │  degrees: [...]│    │ }                  │
          │  ...           │    │                    │
          │ }              │    │                    │
          └────────┬───────┘    └────────┬───────────┘
                   │                     │
                   └─────────┬───────────┘
                             │
                ┌────────────▼────────────┐
                │  Document Metadata Obj  │
                │  {                      │
                │    file_info: {...}     │
                │    entities: {...}      │
                │    sections: {...}      │
                │    is_scanned: bool     │
                │    quality_score: num   │
                │  }                      │
                └────────────┬────────────┘
                             │
                             ▼
                    ┌─────────────────────┐
                    │  OUTPUT: Metadata   │
                    │  Dictionary with    │
                    │  all extracted info │
                    └─────────────────────┘
```

## 🎯 Quality Scoring Flow

```
                    Input: Document Metadata
                              │
                              ▼
                    ┌──────────────────────┐
                    │  Initialize Score    │
                    │  score = 100         │
                    └──────────┬───────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
   ┌────────────┐      ┌────────────────┐    ┌──────────────┐
   │ Is Scanned?│      │ Text Length?   │    │ Sections?    │
   │            │      │                │    │              │
   │ Yes: -20   │      │ >5000: +10     │    │ >=4: +10     │
   │ No: 0      │      │ <1000: -15     │    │ <2: -10      │
   └─────┬──────┘      └────────┬───────┘    └──────┬───────┘
         │                      │                   │
         │                      │                   │
   ┌─────▼─────┐         ┌──────▼──────┐     ┌────▼──────┐
   │ Has Email?│         │ Has Phones? │     │Has Skills?│
   │ Yes: +5   │         │ Yes: +5     │     │ >=5: +10  │
   │ No: 0     │         │ No: 0       │     │ 0: -10    │
   └─────┬─────┘         └──────┬──────┘     └────┬──────┘
         │                      │                 │
         └──────────────────────┼─────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Calculate Final      │
                    │  score = sum(all)     │
                    │  Clamp (0-100)        │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Determine Level      │
                    │                       │
                    │  75+: "HIGH"          │
                    │  50-74: "MEDIUM"      │
                    │  <50: "LOW"           │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │ Output: (score, level)
                    │ (75, "HIGH")         │
                    └──────────────────────┘
```

## 🔐 PII Protection Flow

```
                    Raw Resume Data
         {name, email, phone, raw_text, ...}
                          │
                          ▼
                  ┌───────────────────────┐
                  │ Apply PII Masking      │
                  │                       │
                  │ name → "[NAME]"       │
                  │ email → "[EMAIL]"     │
                  │ phone → "[PHONE]"     │
                  │                       │
                  │ text → protect_pii    │
                  │        _from_text()   │
                  └───────────┬───────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │ Protected Resume Data │
                    │ {                    │
                    │   name: "[NAME]"     │
                    │   email: "[EMAIL]"   │
                    │   phone: "[PHONE]"   │
                    │   skills: [...]      │
                    │   metadata: {...}    │
                    │ }                    │
                    └──────────────────────┘
                              │
                              ▼
                    Safe for LLM Processing
```

## 📈 Entity Extraction Coverage

```
Document Text
     │
     ├─► Emails        ─────────► john@example.com
     │                           jane@company.com
     │
     ├─► Phones        ─────────► +1-555-123-4567
     │                           (555) 234-5678
     │
     ├─► URLs          ─────────► https://linkedin.com/in/john
     │                           https://github.com/johndoe
     │
     ├─► Dates         ─────────► 2020-01-15
     │                           Jan 15, 2020
     │
     ├─► Locations     ─────────► San Francisco, CA
     │                           New York, NY
     │
     ├─► Skills        ─────────► python, javascript, react
     │                           aws, docker, kubernetes
     │
     ├─► Degrees       ─────────► bachelor's, master's, phd
     │
     └─► Companies     ─────────► Microsoft, Google, Apple
```

## 🔗 Integration with LLM

```
┌────────────────────────────────────────────────────────────┐
│                    LLM Input Construction                   │
└─────────────────────────┬──────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
   ┌─────────────┐  ┌────────────┐  ┌──────────────┐
   │Job Descr.   │  │ Candidate  │  │   Document   │
   │(Protected)  │  │ Skills     │  │   Metadata   │
   │             │  │ Experience │  │              │
   │"We're       │  │ Education  │  │Is Scanned: No│
   │looking for  │  │            │  │Sections: 4   │
   │a Python     │  │name: [NAME]│  │Skills Found: 12
   │developer"   │  │            │  │Quality: HIGH │
   └──────┬──────┘  └────────┬───┘  └──────┬───────┘
          │                  │             │
          └──────────────────┼─────────────┘
                             │
                    ┌────────▼────────┐
                    │ Create Prompt   │
                    │ with Context    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Send to OpenAI   │
                    │ GPT-4O-Mini      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Receive Response │
                    │ (JSON)           │
                    └────────┬─────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
        ┌──────────────┐        ┌──────────────────┐
        │ Match %: 85  │        │ Quality: "HIGH"  │
        │ Recom: INT   │        │ Confidence: HIGH │
        │ Strengths: []│        │                  │
        │ Gaps: []     │        │                  │
        └──────────────┘        └──────────────────┘
```

## 📊 Module Dependencies

```
                    API Endpoint
                   (matcher.py)
                         │
                         ▼
                  process_resume_upload()
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
    resume_      resume_protected_    evaluate_
    parser.py    with_metadata()      candidate()
        │                │                │
        ├─────────┬──────┤        ┌──────┤
        │         │      │        │      │
        ▼         ▼      ▼        ▼      ▼
    MetadataExtractor  pii_protector  OpenAI API
        │                │                │
        ├─ Regex patterns                 │
        ├─ PDF parsing                    │
        ├─ Text extraction        (External)
        ├─ Entity extraction
        └─ Section detection

        metadata_analyzer.py
        (Quality scoring)
              │
        ┌─────┴─────┐
        ▼           ▼
    Scoring    Filtering
    Ranking    Analysis
```

## 🔄 Resume Upload Workflow

```
1. User selects resume file
   └─► Uploaded to /matcher/upload endpoint

2. File saved to disk
   └─► UUID-based naming for security

3. Text extraction
   ├─► PDF: PyPDF2 extraction
   ├─► DOCX: python-docx extraction
   └─► TXT: Direct file read

4. Resume parsing
   ├─► Extract: name, email, phone
   ├─► Extract: skills, experience
   └─► Create base resume data

5. Metadata extraction
   ├─► Entity extraction (emails, phones, etc.)
   ├─► Section detection
   ├─► Quality assessment
   └─► Create metadata object

6. PII protection
   ├─► Mask name, email, phone
   ├─► Protect text content
   └─► Create safe version for LLM

7. LLM evaluation
   ├─► Send protected candidate data
   ├─► Send job description
   ├─► Send metadata context
   └─► Get evaluation results

8. Combine results
   ├─► Original resume data
   ├─► Metadata object
   ├─► LLM evaluation results
   ├─► Document quality assessment
   └─► Create final response

9. Stream to client
   └─► Server-Sent Events (SSE)
```

---

This architecture provides a comprehensive metadata extraction system that handles both selectable and non-selectable text documents while maintaining PII protection and improving candidate evaluation through document metadata analysis.
