"""
Lightweight resume parsing utility with comprehensive metadata extraction.
"""
import re
from pathlib import Path
from typing import Tuple, Dict, Any
from PyPDF2 import PdfReader
from docx import Document
from app.utils.pii_protector import protect_pii_from_text, protect_pii_profile
from app.utils.metadata_extractor import MetadataExtractor


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(path)
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    if suffix == ".docx":
        doc = Document(path)
        return "\n".join([p.text for p in doc.paragraphs])
    if suffix == ".doc":
        # Legacy .doc format is not supported by python-docx and will raise 'not a zip' errors.
        # Return empty text to allow downstream handling without crashing.
        return ""
    return path.read_text(errors="ignore")


def extract_email(text: str) -> str:
    match = re.search(r"[\w\.\-+]+@[\w\.\-]+\.\w+", text)
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    match = re.search(r"(\+?\d[\d\-\s]{7,}\d)", text)
    return match.group(0).strip() if match else ""


def extract_name(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if lines:
        first = lines[0]
        # simple heuristic: two capitalized words
        tokens = first.split()
        if len(tokens) <= 4:
            return first
    return ""


def extract_skills(text: str) -> Tuple[list, str]:
    skills = []
    experience = []
    lines = text.splitlines()
    for idx, ln in enumerate(lines):
        lower = ln.lower()
        if "skill" in lower:
            # take line and maybe next line
            skills.append(lines[idx])
            if idx + 1 < len(lines):
                skills.append(lines[idx + 1])
        if any(word in lower for word in ["experience", "worked", "role", "project"]):
            experience.append(ln)
    merged_skills = ", ".join([s.strip() for s in skills if s.strip()])
    experience_summary = " ".join([e.strip() for e in experience[:6]])
    skill_tokens = [token.strip() for token in re.split(r"[,\•;]", merged_skills) if token.strip()]
    return skill_tokens, experience_summary


def parse_resume(path: Path) -> Dict[str, Any]:
    text = extract_text(path)
    email = extract_email(text)
    phone = extract_phone(text)
    name = extract_name(text)
    skills, experience_summary = extract_skills(text)
    return {
        "name": name,
        "email": email,
        "phone": phone,
        "raw_text": text,
        "skills": skills,
        "experience_summary": experience_summary,
    }


def parse_resume_with_metadata(path: Path) -> Dict[str, Any]:
    """
    Parse resume and extract comprehensive metadata including document information.
    Handles both selectable and non-selectable text documents.
    
    Args:
        path: Path to the resume file
        
    Returns:
        Dictionary with parsed resume data and document metadata
    """
    # Get standard resume parsing
    resume_data = parse_resume(path)
    
    # Extract metadata using MetadataExtractor
    extractor = MetadataExtractor()
    # Ensure metadata is a plain dict for downstream consumers
    metadata_obj = extractor.extract_metadata(str(path))
    metadata = extractor.metadata_to_dict(metadata_obj)
    
    # Combine resume and metadata
    enhanced_data = {
        **resume_data,
        "metadata": metadata,
    }
    
    return enhanced_data


def parse_resume_protected(path: Path) -> Dict[str, Any]:
    """
    Parse resume and return with PII masked for safe use with LLM models.
    All sensitive information (name, email, phone, etc.) is masked.
    
    Args:
        path: Path to the resume file
        
    Returns:
        Dictionary with parsed data where PII is masked
    """
    resume_data = parse_resume(path)
    
    # Get the name before masking
    original_name = resume_data.get("name")
    
    # Create protected version with all text fields masked
    protected_data = {
        "name": "[NAME]" if resume_data.get("name") else "",
        "email": "[EMAIL]" if resume_data.get("email") else "",
        "phone": "[PHONE]" if resume_data.get("phone") else "",
        "raw_text": protect_pii_from_text(resume_data.get("raw_text", ""), original_name),
        "skills": resume_data.get("skills", []),  # Skills are generally safe
        "experience_summary": protect_pii_from_text(
            resume_data.get("experience_summary", ""), 
            original_name
        ),
    }
    
    return protected_data


def parse_resume_protected_with_metadata(path: Path) -> Dict[str, Any]:
    """
    Parse resume with PII protection and extract comprehensive metadata.
    Safe for use with LLM models while including document information.
    
    Args:
        path: Path to the resume file
        
    Returns:
        Dictionary with PII-protected resume data and document metadata
    """
    # Get protected resume data
    protected_data = parse_resume_protected(path)
    
    # Extract metadata
    extractor = MetadataExtractor()
    # Ensure metadata is serialized to dict
    metadata_obj = extractor.extract_metadata(str(path))
    metadata = extractor.metadata_to_dict(metadata_obj)
    
    # Combine protected data with metadata
    enhanced_data = {
        **protected_data,
        "metadata": metadata,
    }
    
    return enhanced_data
