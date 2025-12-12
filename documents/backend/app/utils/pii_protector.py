"""
PII Protection utility for masking sensitive information before sending to LLM models.
Uses partial hashing/obfuscation to maintain some identifier information while protecting privacy.
Example: Vaishnavi -> VaisXXXXi, john.smith@company.com -> jo***@****.com
"""
import re
from typing import Dict, Any, List


# Regex patterns for detecting PII
PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"(\+?\d[\d\-\s()]{7,}\d|\b\d{3}[-.]?\d{3}[-.]?\d{4}\b)",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "ipv4": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
    "url": r"https?://\S+|www\.\S+",
    "address": r"\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Circle|Cir|Way|Parkway|Pkwy)",
    "date": r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b",
}

# Compiled regex patterns for performance
COMPILED_PATTERNS = {
    name: re.compile(pattern, re.IGNORECASE) for name, pattern in PATTERNS.items()
}


def obfuscate_name(name: str) -> str:
    """
    Obfuscate a name by showing first 4 chars and last char, replacing middle with X.
    Example: Vaishnavi -> VaisXXXXi
    """
    if not name or len(name) <= 4:
        return "X" * len(name)
    
    first_part = name[:4]
    last_part = name[-1]
    middle_length = len(name) - 5
    return f"{first_part}{'X' * middle_length}{last_part}"


def obfuscate_email(email: str) -> str:
    """
    Obfuscate email by showing first 2 chars, domain first 3 chars.
    Example: john.smith@company.com -> jo***@com***.com
    """
    if "@" not in email:
        return "***@***"
    
    local, domain = email.split("@", 1)
    
    # Show first 2 chars of local part, hide rest with *
    if len(local) <= 2:
        obfuscated_local = local
    else:
        obfuscated_local = local[:2] + "***"
    
    # Show first 3 chars of domain, then ***, then TLD
    if "." in domain:
        domain_name, tld = domain.rsplit(".", 1)
        if len(domain_name) <= 3:
            obfuscated_domain = domain_name + "***." + tld
        else:
            obfuscated_domain = domain_name[:3] + "***." + tld
    else:
        obfuscated_domain = domain[:3] + "***"
    
    return f"{obfuscated_local}@{obfuscated_domain}"


def obfuscate_phone(phone: str) -> str:
    """
    Obfuscate phone number by showing first 3 digits and last 1 digit.
    Example: (555) 123-4567 -> (555) ***4567 or 555-123-4567 -> 555-****7
    """
    # Extract only digits
    digits = re.sub(r"\D", "", phone)
    
    if len(digits) < 4:
        return "***" + digits[-1] if digits else "****"
    
    # Keep first 3 digits and last digit visible, hide the rest
    # Find the pattern to preserve the original format
    if "(" in phone and ")" in phone:
        # Format like (555) 123-4567
        return f"({digits[:3]}) ***{digits[-1]}"
    elif "-" in phone:
        # Format like 555-123-4567
        return f"{digits[:3]}-****{digits[-1]}"
    else:
        # Just digits
        return digits[:3] + "****" + digits[-1]


def obfuscate_url(url: str) -> str:
    """
    Obfuscate URL by showing protocol and first 3 chars of domain.
    Example: https://linkedin.com/in/johndoe -> https://lin***n.com/in/***
    """
    # Extract protocol and domain
    match = re.match(r"(https?://|www\.)?([^/]+)(.*)", url)
    if not match:
        return "***"
    
    protocol = match.group(1) or ""
    domain = match.group(2)
    path = match.group(3) or ""
    
    # Obfuscate domain
    if len(domain) <= 3:
        obfuscated_domain = domain
    else:
        obfuscated_domain = domain[:3] + "***" + (domain[-4:] if len(domain) > 7 else "")
    
    # Hide path details but keep structure
    if path:
        path_parts = path.split("/")
        obfuscated_path = "/".join(["***" if part and not part.startswith(".") else part for part in path_parts])
    else:
        obfuscated_path = ""
    
    return f"{protocol}{obfuscated_domain}{obfuscated_path}"


def obfuscate_address(address: str) -> str:
    """
    Obfuscate address by showing first word (number/street name) and hiding rest.
    Example: 123 Main St, San Francisco, CA -> 123 ***
    """
    parts = address.split()
    if len(parts) == 0:
        return "***"
    # Show first part (street number), hide the rest
    return parts[0] + " ***"


def obfuscate_ssn(ssn: str) -> str:
    """
    Obfuscate SSN by showing last 4 digits.
    Example: 123-45-6789 -> ***-**-6789
    """
    digits = re.sub(r"\D", "", ssn)
    if len(digits) == 9:
        return f"***-**-{digits[-4:]}"
    return "***-**-****"


def obfuscate_pii(pii_type: str, value: str) -> str:
    """
    Obfuscate PII based on type.
    
    Args:
        pii_type: Type of PII (email, phone, name, url, address, ssn, etc.)
        value: The actual PII value to obfuscate
        
    Returns:
        Obfuscated value
    """
    if not value:
        return value
    
    if pii_type == "email":
        return obfuscate_email(value)
    elif pii_type == "phone":
        return obfuscate_phone(value)
    elif pii_type == "name":
        return obfuscate_name(value)
    elif pii_type == "url":
        return obfuscate_url(value)
    elif pii_type == "address":
        return obfuscate_address(value)
    elif pii_type == "ssn":
        return obfuscate_ssn(value)
    else:
        # Default: show first char and last char with X in middle
        if len(value) <= 2:
            return "X" * len(value)
        return value[0] + "X" * (len(value) - 2) + value[-1]


def protect_pii_from_text(text: str, known_name: str = None) -> str:
    """
    Mask all detected PII from the given text using partial obfuscation.
    
    Args:
        text: The text to protect
        known_name: Optional name to specifically mask in the text
        
    Returns:
        Text with PII obfuscated
    """
    if not text:
        return text
    
    protected = text
    
    # Mask emails - use a callback to obfuscate each match
    protected = COMPILED_PATTERNS["email"].sub(
        lambda m: obfuscate_email(m.group(0)), protected
    )
    
    # Mask phone numbers
    protected = COMPILED_PATTERNS["phone"].sub(
        lambda m: obfuscate_phone(m.group(0)), protected
    )
    
    # Mask SSN
    protected = COMPILED_PATTERNS["ssn"].sub(
        lambda m: obfuscate_ssn(m.group(0)), protected
    )
    
    # Mask IPv4 addresses
    protected = COMPILED_PATTERNS["ipv4"].sub(
        lambda m: obfuscate_pii("ipv4", m.group(0)), protected
    )
    
    # Mask URLs
    protected = COMPILED_PATTERNS["url"].sub(
        lambda m: obfuscate_url(m.group(0)), protected
    )
    
    # Mask addresses
    protected = COMPILED_PATTERNS["address"].sub(
        lambda m: obfuscate_address(m.group(0)), protected
    )
    
    # Mask dates (be careful - might match legitimate dates)
    protected = COMPILED_PATTERNS["date"].sub(
        lambda m: "XX-XX-XXXX", protected
    )
    
    # Mask known name if provided
    if known_name and known_name.strip():
        # Create a case-insensitive pattern for the name
        name_pattern = re.compile(re.escape(known_name), re.IGNORECASE)
        protected = name_pattern.sub(
            lambda m: obfuscate_name(m.group(0)), protected
        )
    
    # Mask common name patterns (e.g., "John Smith", "Jane Doe")
    # Look for capitalized word pairs that likely represent names
    name_pattern = re.compile(r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b")
    protected = name_pattern.sub(
        lambda m: obfuscate_name(m.group(1)), protected
    )
    
    return protected


def protect_pii_profile(profile: Dict[str, Any], name: str = None) -> Dict[str, Any]:
    """
    Mask PII in a candidate profile dictionary using partial obfuscation.
    
    Args:
        profile: The profile dictionary to protect
        name: Optional name to mask (usually from full_name field)
        
    Returns:
        New profile dictionary with PII obfuscated
    """
    if not isinstance(profile, dict):
        return profile
    
    protected = dict(profile)  # Shallow copy
    
    # Fields that are direct PII and should be obfuscated
    pii_fields = {
        "full_name": "name",
        "name": "name",
        "email": "email",
        "phone": "phone",
        "address": "address",
        "city": "city",
        "state": "state",
        "zip_code": "zip",
        "ssn": "ssn",
        "date_of_birth": "date",
        "linkedin_url": "url",
        "github_url": "url",
    }
    
    # Direct obfuscation of known PII fields
    for field, pii_type in pii_fields.items():
        if field in protected and protected[field]:
            protected[field] = obfuscate_pii(pii_type, str(protected[field]))
    
    # Fields that contain text needing pattern-based protection
    text_fields = [
        "raw_text",
        "summary",
        "bio",
        "about",
        "cover_letter",
        "experience_summary",
        "experiences",
        "education",
        "certifications",
        "skills_description",
    ]
    
    # Determine the name to use for masking
    mask_name = name or profile.get("full_name") or profile.get("name")
    
    for field in text_fields:
        if field in protected and isinstance(protected[field], str):
            protected[field] = protect_pii_from_text(protected[field], mask_name)
        elif field in protected and isinstance(protected[field], list):
            # Handle lists of strings (e.g., list of experiences)
            protected[field] = [
                protect_pii_from_text(item, mask_name) if isinstance(item, str) else item
                for item in protected[field]
            ]
        elif field in protected and isinstance(protected[field], dict):
            # Handle nested dicts
            protected[field] = {
                k: protect_pii_from_text(v, mask_name) if isinstance(v, str) else v
                for k, v in protected[field].items()
            }
    
    return protected


def protect_job_description(job_description: str) -> str:
    """
    Protect PII in job descriptions using partial obfuscation.
    
    Args:
        job_description: The job description text
        
    Returns:
        Protected job description
    """
    if not job_description:
        return job_description
    
    protected = job_description
    
    # Obfuscate company addresses and contact info
    protected = COMPILED_PATTERNS["email"].sub(
        lambda m: obfuscate_email(m.group(0)), protected
    )
    protected = COMPILED_PATTERNS["phone"].sub(
        lambda m: obfuscate_phone(m.group(0)), protected
    )
    protected = COMPILED_PATTERNS["address"].sub(
        lambda m: obfuscate_address(m.group(0)), protected
    )
    protected = COMPILED_PATTERNS["url"].sub(
        lambda m: obfuscate_url(m.group(0)), protected
    )
    
    return protected


def create_safe_resume_text(resume_text: str, full_name: str = None) -> str:
    """
    Create a safe version of resume text with all PII obfuscated for LLM processing.
    
    Args:
        resume_text: The raw resume text
        full_name: Optional full name of the candidate
        
    Returns:
        Resume text with PII protected
    """
    return protect_pii_from_text(resume_text, full_name)


def get_pii_summary(text: str) -> Dict[str, List[str]]:
    """
    Identify and extract found PII patterns from text (for logging/debugging).
    WARNING: Use carefully - only for audit logging, never return to clients.
    
    Args:
        text: The text to scan
        
    Returns:
        Dictionary mapping PII types to found values
    """
    summary = {}
    
    for pii_type, pattern in COMPILED_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            # Flatten matches if they're tuples (from grouped regex)
            flat_matches = []
            for match in matches:
                if isinstance(match, tuple):
                    flat_matches.extend([m for m in match if m])
                else:
                    flat_matches.append(match)
            summary[pii_type] = list(set(flat_matches))[:5]  # Limit to 5 unique matches per type
    
    return summary
