# Document Metadata Extraction Implementation

## Overview

This implementation provides comprehensive metadata extraction capabilities for documents used in the profile matching system. It can handle both **selectable text documents** (PDFs with native text, DOCX, TXT) and **non-selectable text documents** (scanned PDFs, images with embedded text).

## Key Features

### 1. **Multi-Format Document Support**
- **Selectable Text Documents**: PDF (native text), DOCX, DOC, TXT, Markdown
- **Non-Selectable Documents**: Scanned PDFs, document images
- **Format Detection**: Automatic detection of document type and content characteristics

### 2. **Comprehensive Metadata Extraction**

#### Document Information
- File metadata (name, type, size, path)
- Page count (for PDFs)
- Content type classification (selectable vs. scanned)
- Text length and language detection

#### Entity Extraction
- **Email addresses** - Contact information extraction
- **Phone numbers** - Various formats supported
- **URLs** - Link detection
- **Dates** - Multiple date format support
- **Locations** - Geographic information
- **Skills** - Tech skills and competencies (extensive skill database)
- **Degrees** - Educational qualifications
- **Certifications** - Professional certifications

#### Section Detection
- Automatic detection of common resume sections:
  - Experience
  - Education
  - Skills
  - Projects
  - Certifications
  - Summary/Objective
  - Contact Information

### 3. **Document Quality Assessment**
- Quality scoring (0-100) based on:
  - Document structure (native vs. scanned)
  - Content completeness
  - Section organization
  - Entity extraction richness
- Quality levels: High, Medium, Low

## Module Architecture

### `metadata_extractor.py`
Core metadata extraction module with:
- `DocumentMetadata` - Data class for storing extracted metadata
- `MetadataExtractor` - Main extraction engine
- Entity extraction methods
- Section detection algorithm
- Document type classification

**Key Methods:**
```python
extractor = MetadataExtractor()

# Extract metadata from a document
metadata = extractor.extract_metadata("/path/to/resume.pdf")

# Convert to dictionary
metadata_dict = extractor.metadata_to_dict(metadata)

# Convenience function
metadata = extract_metadata("/path/to/resume.pdf")
```

### `resume_parser.py` (Enhanced)
Enhanced resume parsing with metadata integration:

**New Functions:**
- `parse_resume_with_metadata(path)` - Parse resume and extract metadata
- `parse_resume_protected_with_metadata(path)` - PII-protected parsing with metadata

**Usage:**
```python
from app.utils.resume_parser import parse_resume_with_metadata

# Get resume data with metadata
result = parse_resume_with_metadata(Path("/path/to/resume.pdf"))

# Metadata is included in the result
print(result["metadata"]["entities"]["skills"])
print(result["metadata"]["sections"].keys())
print(result["metadata"]["is_scanned"])
```

### `metadata_analyzer.py`
Analysis and filtering utilities for candidate profiling:
- `MetadataAnalyzer` - Analyze and score metadata

**Key Methods:**
```python
from app.utils.metadata_analyzer import MetadataAnalyzer

# Calculate document quality score
score, quality_level = MetadataAnalyzer.calculate_document_quality_score(metadata)

# Filter candidates by quality
qualified, disqualified = MetadataAnalyzer.filter_candidates_by_metadata(
    candidates, 
    min_quality_score=50.0
)

# Rank candidates by metadata quality
ranked = MetadataAnalyzer.rank_candidates_by_metadata(candidates)

# Extract key metadata for display
key_info = MetadataAnalyzer.extract_key_metadata(metadata)

# Generate summary
summary = MetadataAnalyzer.get_metadata_summary(metadata)
```

### `profile_matcher.py` (Enhanced)
Updated profile matching with metadata integration:

**Enhanced Functions:**
- `evaluate_candidate(candidate_data, job_description, metadata=None)` - Now includes metadata analysis
- `process_resume_upload()` - Extracts metadata during upload processing

**Process Flow:**
1. Resume is uploaded
2. Metadata is extracted from document
3. Resume text is parsed (with PII protection)
4. Metadata and candidate data are sent to LLM for evaluation
5. Results include document quality assessment

## Data Structure

### Metadata Dictionary Format
```json
{
  "file_name": "resume.pdf",
  "file_type": ".pdf",
  "file_size": 245000,
  "file_path": "/path/to/resume.pdf",
  "extracted_at": "2024-11-24T10:30:00.000000",
  "content_type": "application/pdf",
  "page_count": 2,
  "language": "en",
  "has_selectable_text": true,
  "has_images": false,
  "image_count": 0,
  "is_scanned": false,
  "ocr_confidence": null,
  "text_length": 4523,
  "sections": {
    "experience": "content...",
    "education": "content...",
    "skills": "content..."
  },
  "entities": {
    "emails": ["john@example.com"],
    "phones": ["+1-555-123-4567"],
    "urls": ["https://linkedin.com/in/john"],
    "dates": ["2020-01-15", "Jan 15, 2020"],
    "locations": ["San Francisco, CA"],
    "skills": ["python", "javascript", "react"],
    "degrees": ["bachelor's", "master's"],
    "companies": [],
    "certifications": []
  },
  "metadata_tags": {}
}
```

## Integration with Profile Matcher

### Resume Upload Flow
```
1. User uploads resume → process_resume_upload()
2. Document stored on disk
3. Metadata extracted via MetadataExtractor
4. Resume text parsed and PII-protected
5. LLM evaluation includes:
   - Candidate skills and experience
   - Document metadata (quality, format, sections)
   - Job description match
6. Response includes document_quality assessment
7. Results stored with metadata reference
```

### Evaluation Response
```json
{
  "match_percentage": 85,
  "strengths": ["Strong Python skills", "10+ years experience"],
  "gaps": ["No React experience"],
  "technical_alignment": "Very Strong",
  "experience_alignment": "Strong",
  "document_quality": "high",
  "recommendation": "interview",
  "follow_up_questions": ["Tell us about your React learning plans..."],
  "document_metadata": {
    "file_name": "resume.pdf",
    "is_scanned": false,
    "detected_sections": ["experience", "education", "skills"],
    "skills_found": 12,
    ...
  }
}
```

## Handling Non-Selectable Text Documents

### Detection
The system automatically detects scanned documents by checking if PDF text extraction returns minimal content.

**Indicators of Scanned Documents:**
- `is_scanned: true` - Detected as scanned
- `has_selectable_text: false` - No selectable text layers
- `content_type: "scanned_document"` - Classification

### Processing Strategy
For scanned documents:
1. Document is still processed (best-effort text extraction)
2. Quality score is penalized (-20 points)
3. Flag is set for manual review consideration
4. LLM receives metadata indication of scan status

### Future Enhancements
The architecture supports adding OCR capabilities:
```python
# Structure already supports OCR metadata
metadata.ocr_confidence = 0.95  # Confidence score
metadata.entities["text_from_ocr"] = True  # OCR flag
```

## Usage Examples

### Example 1: Extract Metadata Only
```python
from app.utils.metadata_extractor import extract_metadata

metadata = extract_metadata("/uploads/resume.pdf")
print(f"Skills found: {metadata['entities']['skills']}")
print(f"Document quality: {'Scanned' if metadata['is_scanned'] else 'Native'}")
print(f"Sections detected: {list(metadata['sections'].keys())}")
```

### Example 2: Parse Resume with Protected Data and Metadata
```python
from app.utils.resume_parser import parse_resume_protected_with_metadata

data = parse_resume_protected_with_metadata(Path("/uploads/resume.pdf"))
print(f"Name (protected): {data['name']}")  # Shows [NAME]
print(f"Actual skills found: {data['metadata']['entities']['skills']}")
print(f"Document format: {data['metadata']['content_type']}")
```

### Example 3: Rank Candidates by Document Quality
```python
from app.utils.metadata_analyzer import MetadataAnalyzer

# Assuming you have a list of candidates with metadata
ranked = MetadataAnalyzer.rank_candidates_by_metadata(candidates)

for i, candidate in enumerate(ranked[:5]):
    print(f"{i+1}. {candidate['name']} - Quality Score: {candidate['metadata_quality_score']}")
```

### Example 4: Filter and Analyze Candidates
```python
from app.utils.metadata_analyzer import MetadataAnalyzer

qualified, disqualified = MetadataAnalyzer.filter_candidates_by_metadata(
    candidates, 
    min_quality_score=60
)

for candidate in qualified:
    summary = MetadataAnalyzer.get_metadata_summary(candidate["metadata"])
    print(f"\n{candidate['name']}:\n{summary}")
```

## Configuration

### Skill Keywords
The skill extraction uses a predefined set of keywords in `MetadataExtractor.SKILL_KEYWORDS`. To add more skills:

```python
# In metadata_extractor.py
SKILL_KEYWORDS = {
    # Existing skills...
    "new_skill_1",
    "new_skill_2",
}
```

### Quality Score Weights
Adjust quality score calculations in `MetadataAnalyzer.calculate_document_quality_score()`:
- Scanned document penalty: -20 points
- Minimal content penalty: -15 points
- Large content bonus: +10 points
- Well-structured bonus: +10 points
- Rich skills bonus: +10 points

### Minimum Quality Threshold
Set minimum acceptable quality score when filtering:
```python
qualified, disqualified = MetadataAnalyzer.filter_candidates_by_metadata(
    candidates, 
    min_quality_score=75  # Adjust threshold
)
```

## Performance Considerations

### Text Extraction
- **PDF**: Uses PyPDF2, fast even for large files
- **DOCX**: Uses python-docx, efficient for Office documents
- **Plain Text**: Direct file read with error handling

### Entity Extraction
- Uses regex patterns for performance
- Skill matching uses word boundaries to avoid false positives
- Date detection supports common formats

### Section Detection
- Regex-based pattern matching
- Configurable section keywords
- Can be expanded with custom patterns

## Error Handling

All extraction functions handle errors gracefully:
```python
try:
    metadata = extract_metadata(file_path)
except FileNotFoundError:
    print("File not found")
except ValueError as e:
    print(f"Extraction error: {e}")
```

## Testing

Test the metadata extraction:
```python
from pathlib import Path
from app.utils.metadata_extractor import MetadataExtractor

# Test with a real resume
test_file = Path("/path/to/test/resume.pdf")
extractor = MetadataExtractor()
metadata = extractor.extract_metadata(str(test_file))

# Verify extraction
assert "pdf" in metadata.file_type
assert metadata.text_length > 0
assert len(metadata.entities["emails"]) >= 0
print("Metadata extraction working correctly!")
```

## API Responses

The matcher API now includes metadata in responses:

```json
{
  "upload_id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "skills": ["python", "javascript"],
  "match_percentage": 85,
  "recommendation": "interview",
  "document_quality": "high",
  "document_metadata": {
    "file_type": ".pdf",
    "is_scanned": false,
    "detected_sections": ["experience", "education", "skills"],
    "entities": {
      "skills": ["python", "javascript", "react"],
      "degrees": ["bachelor's"]
    }
  }
}
```

## Future Enhancements

1. **OCR for Scanned Documents**: Integrate Tesseract or AWS Textract for better scanned document handling
2. **Language Detection**: Expand language support beyond English
3. **Enhanced NER**: Use spaCy or BERT for better entity recognition
4. **Skill Matching**: ML-based skill extraction and normalization
5. **Resume Parsing Comparison**: Compare against industry-standard libraries
6. **Caching**: Cache metadata extraction results for same documents
7. **Metadata Indexing**: Index metadata for fast search and filtering
8. **Quality Alerts**: Flag suspicious metadata (e.g., no contact info)

## Troubleshooting

### PDF Text Not Extracting
- Check if PDF has selectable text layers
- May need OCR for scanned PDFs
- Use `metadata.has_selectable_text` to detect this

### Skills Not Detected
- Ensure skill keywords are in the SKILL_KEYWORDS set
- Check for variations (e.g., "Node.js" vs "nodejs")
- May need to expand skill database

### Sections Not Detected
- Adjust section keyword patterns in `detect_sections()`
- Some resumes may not follow standard section headers
- Can be expanded with custom patterns

