import json
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

from app.config import settings
from app.utils.openai_client import async_openai_client
from app.utils.resume_parser import (
    parse_resume, 
    parse_resume_protected,
    parse_resume_with_metadata,
    parse_resume_protected_with_metadata
)
from app.utils.pii_protector import protect_job_description, protect_pii_from_text


async def evaluate_candidate(candidate_data: Dict[str, Any], job_description: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Evaluate candidate against job description using LLM.
    Includes document metadata analysis for comprehensive evaluation.
    
    Args:
        candidate_data: Parsed candidate profile (should already be PII-protected)
        job_description: Job description (should already be PII-protected)
        metadata: Optional document metadata for additional context
        
    Returns:
        Evaluation results in JSON format
    """
    # Use global async OpenAI client with SSL configuration
    client = async_openai_client
    
    # Ensure job description is protected before sending to LLM
    safe_job_desc = protect_job_description(job_description)
    
    # Build metadata context if available
    metadata_context = ""
    if metadata:
        document_info = (
            f"\nDocument Information:\n"
            f"- File Type: {metadata.get('file_type', 'unknown')}\n"
            f"- Document Type: {metadata.get('content_type', 'unknown')}\n"
            f"- Selectable Text: {metadata.get('has_selectable_text', False)}\n"
            f"- Is Scanned: {metadata.get('is_scanned', False)}\n"
            f"- Extracted Sections: {', '.join(metadata.get('sections', {}).keys())}\n"
            f"- Found Skills Count: {len(metadata.get('entities', {}).get('skills', []))}\n"
            f"- Found Certifications: {', '.join(metadata.get('entities', {}).get('degrees', [])[:3])}\n"
        )
        metadata_context = document_info
    
    prompt = (
        "You are an expert technical recruiter.\n"
        "Return ONLY JSON.\n"
        "Here is the job description:\n"
        f"{safe_job_desc}\n\n"
        "Here is a candidate profile:\n"
        f"{json.dumps(candidate_data, ensure_ascii=False)}\n"
        f"{metadata_context}\n"
        "Respond with JSON exactly in the following shape:\n"
        "{\n"
        '  "match_percentage": number,\n'
        '  "strengths": ["..."],\n'
        '  "gaps": ["..."],\n'
        '  "technical_alignment": "...",\n'
        '  "experience_alignment": "...",\n'
        '  "document_quality": "high/medium/low",\n'
        '  "recommendation": "hire/interview/reject",\n'
        '  "follow_up_questions": ["..."]\n'
        "}"
    )
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.25,
        max_tokens=400,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content
    return json.loads(content)


async def process_resume_upload(file_bytes: bytes, filename: str, upload_dir: Path, job_description: str) -> Dict[str, Any]:
    """
    Process uploaded resume and evaluate against job description.
    Extracts comprehensive metadata from documents including non-selectable text.
    PII is protected before sending to LLM, but original data is stored for DB records.
    
    Args:
        file_bytes: Resume file content
        filename: Original filename
        upload_dir: Directory to store the uploaded file
        job_description: Job description to match against
        
    Returns:
        Dictionary with parsed data, metadata, evaluation results, and file info
    """
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(filename).suffix or ".txt"
    stored_name = f"{uuid4().hex}{suffix}"
    stored_path = upload_dir / stored_name
    stored_path.write_bytes(file_bytes)

    # Parse the resume with metadata (for storage in DB)
    parsed_with_metadata = parse_resume_with_metadata(stored_path)
    
    # Get protected version with metadata for LLM evaluation
    protected_parsed_with_metadata = parse_resume_protected_with_metadata(stored_path)
    
    # Extract just the protected parsed data (without metadata) for cleaner LLM input
    protected_parsed = {
        k: v for k, v in protected_parsed_with_metadata.items() 
        if k != "metadata"
    }
    metadata = protected_parsed_with_metadata.get("metadata", {})
    
    # Evaluate using protected candidate data, metadata, and job description
    ai_result = await evaluate_candidate(protected_parsed, job_description, metadata)
    
    # PII masking helpers
    def _mask_email(text: str) -> str:
        import re
        if not isinstance(text, str):
            return text
        return re.sub(r"([A-Za-z0-9._%+-]{2})[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", r"\1XXXXX\2", text)

    def _mask_phone(text: str) -> str:
        import re
        if not isinstance(text, str):
            return text
        def repl(m: re.Match) -> str:
            prefix = m.group(1)
            sep = m.group(3)
            tail = m.group(4)
            last = m.group(5)
            masked_tail = re.sub(r"\d", "X", tail)
            return prefix + "XXX" + (sep or "") + masked_tail + last
        pattern = r"(\+?\d[\d\-\s\(\)]{2,}?)(\d{3})([\-\s\)]?)(\d{2,})(\d)"
        return re.sub(pattern, repl, text)

    def _mask_text(text: str) -> str:
        return _mask_phone(_mask_email(text)) if isinstance(text, str) else text

    def _mask_obj(obj):
        if isinstance(obj, str):
            return _mask_text(obj)
        if isinstance(obj, list):
            return [_mask_obj(x) for x in obj]
        if isinstance(obj, dict):
            return {k: _mask_obj(v) for k, v in obj.items()}
        return obj

    # Merge results with original parsed data and metadata, then mask PII for API response
    merged = {
        **parsed_with_metadata,  # Original data with metadata for storage
        **ai_result,  # AI evaluation results
        "file": filename,
        "stored_path": str(stored_path),
        "document_metadata": metadata,  # Explicit metadata field for API responses
    }
    # Mask visible fields commonly displayed in results
    for key in ["name", "email", "phone", "experience_summary"]:
        if key in merged:
            merged[key] = _mask_text(merged[key])
    # Also mask nested metadata entities that may surface
    merged["document_metadata"] = _mask_obj(merged.get("document_metadata", {}))
    merged["skills"] = _mask_obj(merged.get("skills", []))
    
    return merged
