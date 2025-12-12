# AI-Generated Resume Detection Implementation Guide

## Overview

This guide documents the implementation of AI-generated resume detection in the Talent Connect system. The detection system uses multiple heuristic approaches to identify resumes that were likely generated using AI tools like ChatGPT, Claude, or similar LLMs.

## Features

### Detection Methods

The AI detection system uses **6 complementary analysis approaches**:

1. **Common Phrases Analysis (25% weight)**
   - Detects overuse of common AI phrases: "results-driven", "proven track record", "synergy", "leverage", etc.
   - Penalizes repetition (multiple occurrences of same phrase)
   - Normalized by document length to avoid bias toward longer resumes

2. **AI-Specific Patterns (20% weight)**
   - Regex-based detection of AI-typical sentence structures
   - Patterns like "sought to enhance", "implemented...solution", "achieved X% increase"
   - Detects grammatically perfect but unusually formal constructions

3. **Suspicious Perfection Analysis (15% weight)**
   - Detects unrealistic lack of typos
   - Analyzes tense consistency (AI often uses 95%+ consistent tense)
   - Checks sentence structure perfection
   - Evaluates formatting alignment and consistency

4. **Language Metrics (15% weight)**
   - Lexical diversity analysis (AI often has 0.5-0.6 diversity)
   - Average word length (AI tends toward 5-6 characters)
   - Sentence length consistency (AI is more uniform)
   - Passive voice ratio analysis
   - Power word/superlative density detection

5. **Structure Analysis (15% weight)**
   - Detects presence of standard resume sections
   - Analyzes bullet point consistency
   - Evaluates date/timeline coverage
   - Checks for proper section organization

6. **Metadata Analysis (10% weight)**
   - Analyzes PDF/document metadata
   - Detects suspicious producer information
   - Checks creation/modification date patterns

### Risk Levels

Results are categorized into three risk levels:

- **HIGH RISK** (score ≥ 75): Resume is likely AI-generated
- **MEDIUM RISK** (50-74): Resume shows moderate signs of AI generation
- **LOW RISK** (< 50): Resume appears human-written

## Integration Points

### 1. Resume Upload Endpoint

**Location:** `POST /api/v1/interviews/schedule`

When a resume is uploaded during interview scheduling, the system automatically:
- Extracts text from the resume file
- Runs AI detection analysis
- Returns detection results in the response

**Response includes:**
```json
{
  "id": 1,
  "candidate_name": "John Doe",
  "candidate_email": "john@example.com",
  ...
  "ai_detection": {
    "is_ai_generated": true,
    "confidence_score": 78.5,
    "risk_level": "high",
    "indicators": [
      {
        "type": "common_phrases",
        "score": 65.2,
        "message": "Resume contains many common AI-generated phrases"
      }
    ],
    "explanation": "This resume likely contains AI-generated content (high risk). Detected issues: Resume contains many common AI-generated phrases, Multiple AI-specific writing patterns detected"
  }
}
```

### 2. Standalone AI Detection Endpoint

**Location:** `POST /api/v1/interviews/check-resume-ai`

A dedicated endpoint for checking resumes without creating an interview:

```bash
curl -X POST "http://localhost:8000/api/v1/interviews/check-resume-ai" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "resume=@resume.pdf"
```

**Returns:** AI detection result (same structure as above)

## Database Integration

To persist AI detection results, update the Interview model:

```python
# In app/models/interview.py
from sqlalchemy import JSON

class Interview(Base):
    __tablename__ = "interviews"
    
    # ... existing fields ...
    
    # Add these fields to store AI detection results
    ai_detection_score = Column(Float, nullable=True)
    ai_detection_risk_level = Column(String, nullable=True)  # high, medium, low
    ai_detection_result = Column(JSON, nullable=True)  # Full detection result
    ai_flagged = Column(Boolean, default=False)  # Boolean flag for quick filtering
```

### Migration (Alembic)

```python
def upgrade():
    op.add_column('interviews', 
        sa.Column('ai_detection_score', sa.Float(), nullable=True))
    op.add_column('interviews', 
        sa.Column('ai_detection_risk_level', sa.String(), nullable=True))
    op.add_column('interviews', 
        sa.Column('ai_detection_result', sa.JSON(), nullable=True))
    op.add_column('interviews', 
        sa.Column('ai_flagged', sa.Boolean(), default=False))

def downgrade():
    op.drop_column('interviews', 'ai_flagged')
    op.drop_column('interviews', 'ai_detection_result')
    op.drop_column('interviews', 'ai_detection_risk_level')
    op.drop_column('interviews', 'ai_detection_score')
```

## Frontend Integration

### Display AI Detection Results

In the interview dashboard (`frontend/src/pages/Interviews/`):

```jsx
import { Alert, AlertTitle, AlertDescription } from '@/components/atoms';

function InterviewCard({ interview }) {
  return (
    <div className="interview-card">
      {/* ... existing interview info ... */}
      
      {interview.ai_detection && (
        <AIDetectionAlert result={interview.ai_detection} />
      )}
    </div>
  );
}

function AIDetectionAlert({ result }) {
  const riskColors = {
    high: 'bg-red-100 border-red-500',
    medium: 'bg-yellow-100 border-yellow-500',
    low: 'bg-green-100 border-green-500'
  };

  return (
    <Alert className={`border-l-4 ${riskColors[result.risk_level]}`}>
      <AlertTitle className="font-semibold">
        AI Detection: {result.risk_level.toUpperCase()} RISK
        ({result.confidence_score}% confidence)
      </AlertTitle>
      <AlertDescription>
        <p>{result.explanation}</p>
        {result.indicators.length > 0 && (
          <ul className="mt-2 text-sm">
            {result.indicators.map((indicator, idx) => (
              <li key={idx}>• {indicator.message}</li>
            ))}
          </ul>
        )}
      </AlertDescription>
    </Alert>
  );
}
```

### Add to Resume Upload Form

```jsx
function ResumeUploadForm() {
  const [aiDetectionResult, setAiDetectionResult] = useState(null);
  const [isChecking, setIsChecking] = useState(false);

  const handleResumeChange = async (file) => {
    if (file) {
      setIsChecking(true);
      const formData = new FormData();
      formData.append('resume', file);
      
      try {
        const response = await fetch('/api/v1/interviews/check-resume-ai', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${getToken()}`
          },
          body: formData
        });
        
        if (response.ok) {
          const result = await response.json();
          setAiDetectionResult(result);
        }
      } catch (error) {
        console.error('Error checking resume:', error);
      } finally {
        setIsChecking(false);
      }
    }
  };

  return (
    <div>
      <input 
        type="file" 
        onChange={(e) => handleResumeChange(e.target.files[0])}
        disabled={isChecking}
      />
      
      {isChecking && <p>Analyzing resume for AI generation...</p>}
      
      {aiDetectionResult && (
        <AIDetectionAlert result={aiDetectionResult} />
      )}
    </div>
  );
}
```

## Configuration Options

### Adjusting Detection Sensitivity

In `app/utils/ai_detection.py`, you can adjust confidence thresholds:

```python
# In AIResumeDetector.detect_ai_generated()

# Change these thresholds to adjust sensitivity:
if confidence_score >= 75:      # Increase to 80+ for stricter detection
    risk_level = "high"
elif confidence_score >= 50:    # Adjust middle threshold
    risk_level = "medium"
```

### Adjusting Component Weights

Modify the weighted scoring calculation:

```python
# Current weights sum to 1.0
weighted_score = (
    phrase_score * 0.25 +       # Increase for stricter phrase detection
    pattern_score * 0.20 +      
    perfection_score * 0.15 +   
    language_score * 0.15 +     
    structure_score * 0.15 +    
    metadata_score * 0.10       
)
```

### Adding Custom AI Phrases

Extend the common phrases list in `AIResumeDetector`:

```python
AI_COMMON_PHRASES = {
    "results-driven": 5,
    "synergy": 5,
    # Add your custom phrases:
    "your-phrase-here": 4,  # Weight from 1-5
}
```

## Testing

### Run Unit Tests

```bash
cd backend
pytest tests/test_ai_detection.py -v
```

### Test Cases Included

1. ✅ Human-written resume detection
2. ✅ AI-generated resume with common phrases
3. ✅ Suspicious perfection detection
4. ✅ Empty/minimal resume handling
5. ✅ Specific AI pattern detection
6. ✅ Metadata-based detection
7. ✅ Confidence score range validation
8. ✅ Detailed analysis structure validation
9. ✅ Indicators presence when AI detected

## API Examples

### Check Resume During Upload

```bash
curl -X POST "http://localhost:8000/api/v1/interviews/schedule" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "candidate_name=John Doe" \
  -F "role=Software Engineer" \
  -F "resume=@path/to/resume.pdf" \
  -F "date=2025-01-15" \
  -F "time=10:00"
```

### Standalone Check

```bash
curl -X POST "http://localhost:8000/api/v1/interviews/check-resume-ai" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "resume=@path/to/resume.pdf" | jq
```

Response:
```json
{
  "is_ai_generated": true,
  "confidence_score": 78.5,
  "risk_level": "high",
  "indicators": [
    {
      "type": "common_phrases",
      "score": 65.2,
      "message": "Resume contains many common AI-generated phrases"
    },
    {
      "type": "ai_patterns",
      "score": 72.1,
      "message": "Multiple AI-specific writing patterns detected"
    }
  ],
  "explanation": "This resume likely contains AI-generated content (high risk). Detected issues: Resume contains many common AI-generated phrases, Multiple AI-specific writing patterns detected",
  "detailed_analysis": {
    "common_phrases_score": 65.2,
    "ai_patterns_score": 72.1,
    "perfection_score": 45.0,
    "language_metrics_score": 38.5,
    "structure_score": 55.0,
    "metadata_score": 0.0
  }
}
```

## Limitations & Improvements

### Current Limitations

1. **Text extraction dependency**: Quality depends on accurate text extraction
2. **Language bias**: Optimized for English resumes
3. **False positives**: Professional/formal writing may trigger flags
4. **Evolution**: AI writing improves constantly, patterns may become outdated

### Future Enhancements

1. **API Integration**: Add GPT-based zero-shot classification
   ```python
   # Pseudocode for future enhancement
   from openai import OpenAI
   client = OpenAI()
   response = client.chat.completions.create(
       model="gpt-4",
       messages=[{
           "role": "user",
           "content": f"Is this resume AI-generated? {resume_text}"
       }]
   )
   ```

2. **Machine Learning Model**: Train a classifier on known AI/human resumes
3. **Watermark Detection**: Detect AI-specific watermarks in PDF metadata
4. **Multi-language Support**: Add detection for resumes in other languages
5. **Confidence Intervals**: Provide uncertainty ranges instead of single scores
6. **User Feedback Loop**: Let HR teams mark false positives to improve accuracy

## Troubleshooting

### Detection Too Sensitive
- Lower the confidence thresholds (adjust from 75/50 to 80/60)
- Reduce weights for phrase and pattern scoring

### Detection Not Working
- Check that `extract_text()` is properly extracting resume content
- Verify file permissions in `UPLOAD_DIR`
- Check logs for import errors

### Performance Issues
- Detection adds ~50-200ms per resume
- Cache results for frequently accessed interviews
- Consider async processing for batch checks

## Files Modified/Created

```
backend/
├── app/utils/
│   └── ai_detection.py (NEW) - Core detection logic
├── app/api/v1/
│   └── interviews.py (MODIFIED) - Added detection endpoints
├── app/schemas/
│   └── interview.py (MODIFIED) - Added AIDetectionResult schema
├── tests/
│   └── test_ai_detection.py (NEW) - Comprehensive test suite
└── [models/interview.py] (TODO) - Add DB fields for storage

frontend/
└── [src/pages/Interviews/] (TODO) - UI integration examples
```

## Support & Feedback

For issues, suggestions, or improvements to the AI detection system, please document:
1. Example resume(s) that triggered false positives/negatives
2. Expected vs. actual detection results
3. Any patterns or phrases not being detected
