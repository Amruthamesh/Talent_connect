# Frontend AI Detection - Visual Guide

## Interview Scheduling Page with AI Detection

### 📋 Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│                    Schedule Interview                        │
│           Create a new interview session with               │
│        AI-powered resume screening                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Candidate Information                                        │
│                                                              │
│ Candidate Name *          │                                  │
│ [Enter candidate name_____]                                  │
│                                                              │
│ Email Address            │                                  │
│ [candidate@example.com___]                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Position Details                                             │
│                                                              │
│ Role *                   │ Company                          │
│ [Senior Engineer______] │ [Company Name________]           │
│                                                              │
│ Interview Round                                             │
│ [Round 1 - Initial Screening ▼]                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Resume & AI Detection                                        │
│                                                              │
│ [📎 Choose Resume]                                           │
│ 📄 resume.pdf                                               │
│                                                              │
│ 🔍 Analyzing resume for AI generation...                    │
│    [Spinner Animation]                                      │
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 🚨 AI Generation Detection             [HIGH RISK]      ││
│ │ This resume is likely AI-generated                     ││
│ │                                                         ││
│ │ Confidence Score                                        ││
│ │ ████████████████████░░░░░░░░░░░░░░░░░░░░░░ 78.5%     ││
│ │                                                         ││
│ │ Detected Issues:                                        ││
│ │ • common_phrases: Resume contains many common          ││
│ │   AI-generated phrases (Score: 100%)                   ││
│ │ • ai_patterns: Multiple AI-specific writing patterns   ││
│ │   detected (Score: 72%)                                ││
│ │                                                         ││
│ │ [View Detailed Analysis]                                ││
│ │   common_phrases_score:    100%                        ││
│ │   ai_patterns_score:        72%                        ││
│ │   perfection_score:         45%                        ││
│ │   language_metrics_score:   38%                        ││
│ │   structure_score:          55%                        ││
│ │   metadata_score:            0%                        ││
│ │                                                         ││
│ │ This resume shows moderate signs of AI generation.     ││
│ │ Detected issues: Resume contains many common           ││
│ │ AI-generated phrases...                                ││
│ └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Schedule Details                                             │
│                                                              │
│ Date *                   │ Time *                           │
│ [2025-01-15______]     │ [14:30_____]                      │
│                                                              │
│ Notes                                                        │
│ ┌──────────────────────────────────────────────────────────┐
│ │Add any additional notes...                               │
│ │                                                          │
│ │                                                          │
│ │                                                          │
│ └──────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ⚠️  High Risk AI Detection                                  │
│ This resume shows strong indicators of AI generation.       │
│ Proceed with caution.                                       │
└─────────────────────────────────────────────────────────────┘

[📅 Schedule Interview]  [Clear Form]
```

## 🎨 AI Detection Alert States

### HIGH RISK (Confidence > 75%)
```
┌─────────────────────────────────────────────────────────────┐
│ 🚨 AI Generation Detection                    [HIGH RISK]    │
│ This resume is likely AI-generated                          │
│                                                              │
│ Confidence Score                                            │
│ ████████████████████░░░░░░░░░░░░░░░░░░░░░░ 78.5%         │
│                                                              │
│ Detected Issues:                                            │
│ • common_phrases: Resume contains many common AI-generated │
│   phrases (Score: 100%)                                     │
│ • ai_patterns: Multiple AI-specific writing patterns       │
│   detected (Score: 72%)                                     │
└─────────────────────────────────────────────────────────────┘
```

### MEDIUM RISK (Confidence 50-74%)
```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️  AI Generation Detection                  [MEDIUM RISK]   │
│ This resume shows signs of AI generation                    │
│                                                              │
│ Confidence Score                                            │
│ ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 50.5%         │
│                                                              │
│ Detected Issues:                                            │
│ • common_phrases: Resume contains many common AI-generated │
│   phrases (Score: 100%)                                     │
└─────────────────────────────────────────────────────────────┘
```

### LOW RISK (Confidence < 50%)
```
┌─────────────────────────────────────────────────────────────┐
│ ✅ AI Generation Detection                     [LOW RISK]    │
│ This resume appears to be human-written                     │
│                                                              │
│ Confidence Score                                            │
│ ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  6.3%        │
│                                                              │
│ No specific indicators detected.                            │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Detailed Analysis Breakdown

When user clicks "View Detailed Analysis":

```
Analysis Scores:
┌─────────────────────────┬──────────┐
│ common_phrases_score    │ 100%     │
│ ai_patterns_score       │  72%     │
│ perfection_score        │  45%     │
│ language_metrics_score  │  38%     │
│ structure_score         │  55%     │
│ metadata_score          │   0%     │
└─────────────────────────┴──────────┘
```

## 🔄 User Flow

### Scenario 1: Human-Written Resume
```
1. User fills form
2. User uploads resume.pdf
3. [Analysis starts]
   ✓ Text extraction
   ✓ Pattern analysis
   ✓ Phrase detection
   ✓ Metadata check
4. Result: ✅ LOW RISK (6.3%)
5. No warning shown
6. User can submit form
7. Interview scheduled successfully
```

### Scenario 2: AI-Generated Resume
```
1. User fills form
2. User uploads resume_ai.pdf
3. [Analysis starts]
   ✓ Text extraction
   ✓ Pattern analysis (Detects AI phrases)
   ✓ Perfection scoring (Suspicious consistency)
   ✓ Metadata check
4. Result: 🚨 HIGH RISK (78.5%)
5. Warning banner appears
6. User attempts to submit
7. Confirmation dialog appears:
   "⚠️ This resume shows HIGH RISK of AI generation. 
    Are you sure you want to schedule this interview?"
8. User clicks OK to proceed
9. Interview scheduled (flagged for review)
```

### Scenario 3: Mixed/Borderline Resume
```
1. User fills form
2. User uploads resume_mixed.pdf
3. [Analysis starts]
   ✓ Text extraction
   ✓ Pattern analysis (Some AI phrases)
   ✓ Structure check
   ✓ Metadata check
4. Result: ⚠️ MEDIUM RISK (50.5%)
5. Info alert shown (caution but not blocking)
6. User can submit form
7. Interview scheduled (flagged for review)
```

## 💻 Component Interactions

### Resume Upload Component
```javascript
<ResumeUpload 
  onFileSelect={(file) => handleResumeSelect(file)}
  onAIDetection={(result) => handleAIDetection(result)}
/>

// When file is selected:
1. File validation
2. Show spinner
3. Upload to /api/v1/interviews/check-resume-ai
4. Display result
5. Update form state
6. Show warning if high risk
```

### AI Detection Alert Component
```javascript
<AIDetectionAlert result={aiDetection} />

// Displays:
- Icon + Title + Risk Badge
- Confidence Score with progress bar
- List of detected issues
- Collapsible detailed analysis
- Human-readable explanation
```

## 🎯 Key Features

✅ **Real-Time Analysis**
- Instant feedback as file uploads
- Loading animation during processing
- Immediate results display

✅ **Risk-Based Alerts**
- Color-coded (red/orange/green)
- Clear messaging
- Actionable indicators

✅ **Detailed Transparency**
- Breakdown of all scoring methods
- Confidence percentage
- Specific phrases/patterns detected
- Detailed analysis expandable

✅ **Smart Blocking**
- High-risk resumes require confirmation
- Don't block submission (user's choice)
- Easy to override if needed
- Records decision in system

✅ **Responsive Design**
- Mobile-friendly layout
- Touch-friendly upload
- Responsive alerts
- Mobile-optimized forms

## 🔗 Integration Points

1. **Resume Upload**
   - Hooks into existing form
   - Transparent integration
   - No friction to flow

2. **API Communication**
   - Async file upload
   - Error handling
   - Token-based auth

3. **State Management**
   - Detection result stored
   - Warning state tracked
   - Form submission aware

4. **User Feedback**
   - Clear explanations
   - Visual indicators
   - Actionable next steps

## 📱 Mobile Experience

On mobile devices:
- Single column layout
- Touch-friendly buttons
- Swipeable alerts
- Readable text sizes
- Optimized spacing

```
[Candidate Name___]

[Email____________]

[Role____________]

[Interview Round  ▼]

[📎 Upload Resume]

[High Risk Alert (expandable)]

[Schedule Date  ]

[Schedule Time  ]

[Notes]

[Schedule Interview]
```
