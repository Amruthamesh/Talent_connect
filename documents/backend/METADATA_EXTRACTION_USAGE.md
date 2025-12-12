# Metadata Extraction - Practical Usage Guide

## Quick Start

### 1. Extract Metadata from a Resume
```python
from app.utils.metadata_extractor import extract_metadata

# Simple one-liner
metadata = extract_metadata("/path/to/resume.pdf")

# Check document type
print(f"Is scanned: {metadata['is_scanned']}")
print(f"Skills found: {metadata['entities']['skills']}")
print(f"Sections: {list(metadata['sections'].keys())}")
```

### 2. Parse Resume with Metadata (Unprotected)
```python
from pathlib import Path
from app.utils.resume_parser import parse_resume_with_metadata

data = parse_resume_with_metadata(Path("/path/to/resume.pdf"))

# Access resume fields
print(f"Name: {data['name']}")
print(f"Email: {data['email']}")
print(f"Skills: {data['skills']}")

# Access metadata
print(f"Document type: {data['metadata']['content_type']}")
print(f"Extracted sections: {data['metadata']['sections'].keys()}")
```

### 3. Parse Resume with Metadata (PII Protected)
```python
from pathlib import Path
from app.utils.resume_parser import parse_resume_protected_with_metadata

data = parse_resume_protected_with_metadata(Path("/path/to/resume.pdf"))

# PII is masked
print(f"Name: {data['name']}")  # Shows "[NAME]"
print(f"Email: {data['email']}")  # Shows "[EMAIL]"

# Skills and metadata are still available
print(f"Skills: {data['skills']}")
print(f"Metadata: {data['metadata']}")
```

### 4. Analyze Document Quality
```python
from app.utils.metadata_analyzer import MetadataAnalyzer

# Calculate quality score
score, quality_level = MetadataAnalyzer.calculate_document_quality_score(metadata)
print(f"Document quality: {quality_level} ({score}/100)")

# Get readable summary
summary = MetadataAnalyzer.get_metadata_summary(metadata)
print(summary)
```

### 5. Filter Candidates by Document Quality
```python
from app.utils.metadata_analyzer import MetadataAnalyzer

# Assuming candidates is a list of resume parsing results
qualified, disqualified = MetadataAnalyzer.filter_candidates_by_metadata(
    candidates, 
    min_quality_score=60.0
)

print(f"Qualified: {len(qualified)}")
print(f"Disqualified: {len(disqualified)}")
```

## Common Workflows

### Workflow 1: Resume Upload and Evaluation (Current Implementation)
```python
from pathlib import Path
from app.services.ai.profile_matcher import process_resume_upload

# This is called automatically in the matcher API
result = await process_resume_upload(
    file_bytes=resume_bytes,
    filename="john_doe_resume.pdf",
    upload_dir=Path("/uploads"),
    job_description="We're looking for a Python developer..."
)

# Result includes:
# - name, email, phone, skills (from resume parsing)
# - metadata (file info, entities, sections)
# - match_percentage, recommendation (from LLM evaluation)
# - document_quality (assessment based on metadata)
```

### Workflow 2: Batch Process Multiple Resumes
```python
from pathlib import Path
from app.utils.resume_parser import parse_resume_with_metadata
from app.utils.metadata_analyzer import MetadataAnalyzer

resume_dir = Path("/uploads/batch")
results = []

for resume_file in resume_dir.glob("*.pdf"):
    try:
        data = parse_resume_with_metadata(resume_file)
        results.append(data)
    except Exception as e:
        print(f"Error processing {resume_file}: {e}")

# Rank by document quality
ranked = MetadataAnalyzer.rank_candidates_by_metadata(results)

for candidate in ranked:
    print(f"{candidate['name']}: {candidate['metadata_quality_level']} quality")
```

### Workflow 3: Find Candidates with Specific Skills
```python
from pathlib import Path
from app.utils.resume_parser import parse_resume_with_metadata

target_skills = {"python", "javascript", "react"}

resume_dir = Path("/uploads")
matching_candidates = []

for resume_file in resume_dir.glob("*.pdf"):
    data = parse_resume_with_metadata(resume_file)
    found_skills = set(data['metadata']['entities']['skills'])
    
    if found_skills & target_skills:  # Intersection
        matching_candidates.append({
            "name": data['name'],
            "matched_skills": list(found_skills & target_skills),
            "all_skills": found_skills
        })

for candidate in matching_candidates:
    print(f"{candidate['name']}: {', '.join(candidate['matched_skills'])}")
```

### Workflow 4: Quality Report for Hiring Team
```python
from pathlib import Path
from app.utils.resume_parser import parse_resume_with_metadata
from app.utils.metadata_analyzer import MetadataAnalyzer

resume_dir = Path("/uploads")
quality_report = {
    "total_resumes": 0,
    "high_quality": 0,
    "medium_quality": 0,
    "low_quality": 0,
    "scanned_documents": 0,
    "details": []
}

for resume_file in resume_dir.glob("*.pdf"):
    data = parse_resume_with_metadata(resume_file)
    metadata = data['metadata']
    
    score, level = MetadataAnalyzer.calculate_document_quality_score(metadata)
    
    quality_report["total_resumes"] += 1
    quality_report[f"{level}_quality"] += 1
    
    if metadata['is_scanned']:
        quality_report["scanned_documents"] += 1
    
    quality_report["details"].append({
        "name": data['name'],
        "file": metadata['file_name'],
        "quality": level,
        "score": score,
        "is_scanned": metadata['is_scanned'],
        "skills_found": len(metadata['entities']['skills'])
    })

# Print report
print(f"\n=== Quality Report ===")
print(f"Total Resumes: {quality_report['total_resumes']}")
print(f"High Quality: {quality_report['high_quality']}")
print(f"Medium Quality: {quality_report['medium_quality']}")
print(f"Low Quality: {quality_report['low_quality']}")
print(f"Scanned Documents: {quality_report['scanned_documents']}")

for detail in quality_report["details"]:
    print(f"\n{detail['name']} - {detail['quality'].upper()} (Score: {detail['score']})")
    if detail['is_scanned']:
        print("  ⚠️  Scanned document - may need manual review")
    print(f"  Skills detected: {detail['skills_found']}")
```

### Workflow 5: Resume Completeness Check
```python
from pathlib import Path
from app.utils.resume_parser import parse_resume_with_metadata

def check_completeness(resume_path: Path) -> dict:
    """Check how complete a resume is"""
    data = parse_resume_with_metadata(resume_path)
    metadata = data['metadata']
    entities = metadata['entities']
    sections = metadata['sections']
    
    completeness = {
        "has_contact_info": bool(entities['emails'] or entities['phones']),
        "has_skills": len(entities['skills']) > 0,
        "has_education": len(entities['degrees']) > 0,
        "has_experience": "experience" in sections,
        "is_well_structured": len(sections) >= 4,
        "completeness_score": 0
    }
    
    # Calculate completeness score
    score = 0
    if completeness["has_contact_info"]:
        score += 20
    if completeness["has_skills"]:
        score += 20
    if completeness["has_education"]:
        score += 20
    if completeness["has_experience"]:
        score += 20
    if completeness["is_well_structured"]:
        score += 20
    
    completeness["completeness_score"] = score
    
    return completeness

# Usage
result = check_completeness(Path("/path/to/resume.pdf"))
print(f"Completeness: {result['completeness_score']}/100")
for key, value in result.items():
    if key != "completeness_score":
        print(f"  {key}: {value}")
```

## Entity Extraction Details

### Email Extraction
```python
emails = metadata['entities']['emails']
# Returns: ['john@example.com', 'john.doe@company.com']
```

### Phone Number Extraction
```python
phones = metadata['entities']['phones']
# Returns: ['+1-555-123-4567', '(555) 123-4567']
```

### URL Extraction
```python
urls = metadata['entities']['urls']
# Returns: ['https://linkedin.com/in/johndoe', 'https://github.com/johndoe']
```

### Date Extraction
```python
dates = metadata['entities']['dates']
# Returns: ['2020-01-15', 'Jan 15, 2020', '2020-01-15']
```

### Location Extraction
```python
locations = metadata['entities']['locations']
# Returns: ['San Francisco, CA', 'New York, NY']
```

### Skills Extraction
```python
skills = metadata['entities']['skills']
# Returns: ['python', 'javascript', 'react', 'aws', 'docker']
```

### Degree Extraction
```python
degrees = metadata['entities']['degrees']
# Returns: ["bachelor's", "master's", "phd"]
```

## Section Detection

### Available Section Types
```python
sections = metadata['sections']
# Returns dict with keys like:
# - 'experience'
# - 'education'
# - 'skills'
# - 'projects'
# - 'certifications'
# - 'summary'
# - 'contact'

# Each section contains the text content
for section_name, section_content in sections.items():
    print(f"\n=== {section_name.upper()} ===")
    print(section_content[:200])  # First 200 chars
```

## Document Type Handling

### Detecting Scanned Documents
```python
metadata = extract_metadata("/path/to/resume.pdf")

if metadata['is_scanned']:
    print("⚠️  This is a scanned document")
    print("Confidence in text extraction may be lower")
    # Take additional actions for scanned docs
else:
    print("✓ Native PDF with selectable text")
```

### Document Type Classification
```python
content_type = metadata['content_type']

if content_type == 'selectable_text':
    print("High quality text extraction")
elif content_type == 'scanned_document':
    print("Consider OCR for better text extraction")
else:
    print(f"Document type: {content_type}")
```

## Performance Tips

### 1. Cache Metadata Results
```python
from pathlib import Path
import pickle

def get_or_extract_metadata(resume_path: Path, cache_dir: Path = Path(".cache")):
    """Extract metadata with caching"""
    cache_dir.mkdir(exist_ok=True)
    
    # Create cache file name from resume file
    cache_file = cache_dir / f"{resume_path.stem}.pkl"
    
    if cache_file.exists():
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    
    # Extract if not cached
    from app.utils.metadata_extractor import extract_metadata
    metadata = extract_metadata(str(resume_path))
    
    # Cache for future use
    with open(cache_file, 'wb') as f:
        pickle.dump(metadata, f)
    
    return metadata
```

### 2. Batch Processing with Progress
```python
from pathlib import Path
from app.utils.resume_parser import parse_resume_with_metadata

def batch_process_resumes(resume_dir: Path):
    """Process multiple resumes with progress tracking"""
    files = list(resume_dir.glob("*.pdf"))
    total = len(files)
    
    results = []
    for i, resume_file in enumerate(files, 1):
        try:
            data = parse_resume_with_metadata(resume_file)
            results.append(data)
            print(f"[{i}/{total}] Processed {resume_file.name}")
        except Exception as e:
            print(f"[{i}/{total}] ERROR {resume_file.name}: {e}")
    
    return results
```

## Error Handling

### Safe Metadata Extraction
```python
from pathlib import Path
from app.utils.metadata_extractor import extract_metadata

def safe_extract_metadata(file_path: str) -> dict:
    """Safely extract metadata with error handling"""
    try:
        metadata = extract_metadata(file_path)
        return {
            "success": True,
            "metadata": metadata
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "File not found",
            "file_path": file_path
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "file_path": file_path
        }
```

## API Integration

### In FastAPI Endpoint
```python
from fastapi import UploadFile, File
from pathlib import Path
from app.utils.resume_parser import parse_resume_with_metadata

@router.post("/analyze-resume")
async def analyze_resume(file: UploadFile = File(...)):
    """Endpoint that returns metadata along with parsing"""
    
    # Save uploaded file
    file_path = Path(f"/tmp/{file.filename}")
    with open(file_path, 'wb') as f:
        f.write(await file.read())
    
    try:
        # Parse with metadata
        data = parse_resume_with_metadata(file_path)
        
        return {
            "success": True,
            "name": data['name'],
            "email": data['email'],
            "skills": data['skills'],
            "metadata": {
                "file_type": data['metadata']['file_type'],
                "is_scanned": data['metadata']['is_scanned'],
                "sections": list(data['metadata']['sections'].keys()),
                "skills_count": len(data['metadata']['entities']['skills'])
            }
        }
    finally:
        file_path.unlink()  # Clean up
```

## Troubleshooting

### Issue: No skills detected
**Solution 1**: Check skill keywords
```python
from app.utils.metadata_extractor import MetadataExtractor

# Verify your skill is in the database
skill_to_find = "kubernetes"
if skill_to_find in MetadataExtractor.SKILL_KEYWORDS:
    print("Skill is in database")
else:
    print("Need to add this skill to SKILL_KEYWORDS")
```

**Solution 2**: Extract raw text and check
```python
metadata = extract_metadata("/path/to/resume.pdf")
raw_text = metadata['raw_text']
if "kubernetes" in raw_text.lower():
    print("Text contains 'kubernetes' but not recognized")
    print("May need to update skill extraction")
```

### Issue: PDF text not extracting
```python
from app.utils.metadata_extractor import extract_metadata

metadata = extract_metadata("/path/to/resume.pdf")

if not metadata['has_selectable_text']:
    print("⚠️  PDF has no selectable text layers")
    print("This is likely a scanned document")
    print("Consider using OCR for better extraction")
else:
    print(f"✓ Extracted {metadata['text_length']} characters")
```

### Issue: Sections not detected
```python
metadata = extract_metadata("/path/to/resume.pdf")

if len(metadata['sections']) == 0:
    print("No sections detected")
    print("Resume may not follow standard structure")
    print("Raw text length:", metadata['text_length'])
    
    # Use entities instead
    print("Found via entities:")
    for entity_type, values in metadata['entities'].items():
        if values:
            print(f"  {entity_type}: {values}")
```

