from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel

from app.core.auth import get_current_active_user
from app.core.permissions import require_permission
from app.models.user import User


router = APIRouter(prefix="/jobs", tags=["Jobs"])


# Schemas
class JobDescriptionRequest(BaseModel):
    """Request schema for JD generation"""
    role: str
    experience: str
    skills: List[str]
    company_context: str
    department: Optional[str] = None


class JobDescriptionResponse(BaseModel):
    """Response schema for generated JD"""
    content: str
    role: str
    generated_at: str
    metadata: dict


class ProfileMatchRequest(BaseModel):
    """Request schema for profile matching"""
    job_description: str
    resumes: List[str]  # URLs or file paths


class ProfileMatchResponse(BaseModel):
    """Response schema for profile matching"""
    matches: List[dict]
    total_candidates: int


# Endpoints
from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_active_user
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.jobs import (
    GenerateJDRequest, GenerateJDResponse,
    ExplainJDRequest, ExplainJDResponse,
    RewriteJDRequest, RewriteJDResponse,
    SkillAutocompleteRequest, SkillAutocompleteResponse,
    SkillSuggestion,
    ChatBuilderRequest, ChatBuilderResponse
)
from app.services.ai.jd_generator import JDGeneratorAgent
from app.services.ai.job_builder_chat import JobBuilderChatAgent
from app.services.skills_database import search_skills, get_skill_categories

router = APIRouter(prefix="/jobs", tags=["Jobs"])
def _mask_email(text: str) -> str:
    import re
    if not isinstance(text, str):
        return text
    return re.sub(r"([A-Za-z0-9._%+-]{2})[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", r"\1XXXXX\2", text)

def _mask_phone(text: str) -> str:
    import re
    if not isinstance(text, str):
        return text
    # Generic masking: preserve leading symbol/digit and last digit, mask middle digits
    def repl(m: re.Match) -> str:
        prefix = m.group(1)
        sep = m.group(3)
        tail = m.group(4)
        last = m.group(5)
        masked_tail = re.sub(r"\d", "X", tail)
        return prefix + "XXX" + (sep or "") + masked_tail + last
    pattern = r"(\+?\d[\d\-\s\(\)]{2,}?)(\d{3})([\-\s\)]?)(\d{2,})(\d)"
    return re.sub(pattern, repl, text)

def _mask_pii_text(text: str) -> str:
    text = _mask_email(text)
    text = _mask_phone(text)
    return text

def _mask_pii_in_obj(obj):
    # Recursively mask strings in nested structures
    if isinstance(obj, str):
        return _mask_pii_text(obj)
    if isinstance(obj, list):
        return [_mask_pii_in_obj(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _mask_pii_in_obj(v) for k, v in obj.items()}
    return obj


@router.post("/generate-jd", response_model=GenerateJDResponse)
async def generate_job_description(
    request: GenerateJDRequest,
    current_user: User = Depends(require_permission("jobs.generate_jd"))
):
    """
    Generate comprehensive job description with AI
    
    Returns:
    - Structured JD content
    - Skill matrix with proficiency levels
    - Salary benchmark
    - Strategic insights
    """
    try:
        agent = JDGeneratorAgent()
        
        # Auto-generate expectations if not provided
        expectations = request.expectations
        if not expectations:
            expectations = f"Drive excellence as a {request.seniority} {request.role}, delivering high-quality results and contributing to team success."
        
        # Normalize company_tone to known buckets if possible; otherwise pass through free text
        tone_raw = (request.company_tone or "").strip().lower()
        tone_map = {
            "formal": "formal",
            "startup": "startup",
            "mnc": "mnc",
            "tech": "tech",
        }
        normalized_tone = None
        for key in tone_map.keys():
            if key in tone_raw:
                normalized_tone = tone_map[key]
                break
        company_tone = normalized_tone or request.company_tone

        result = await agent.generate_jd(
            role=request.role,
            seniority=request.seniority,
            expectations=expectations,
            must_have_skills=request.must_have_skills,
            preferred_skills=request.preferred_skills,
            company_tone=company_tone,
            department=request.department,
            location=request.location
        )
        # Mask PII in returned content before responding
        masked = _mask_pii_in_obj(result)
        return masked
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate JD: {str(e)}")


@router.post("/explain-jd", response_model=ExplainJDResponse)
async def explain_jd_to_candidate(
    request: ExplainJDRequest,
    current_user: User = Depends(require_permission("jobs.generate_jd"))
):
    """
    Translate JD into candidate-friendly explanation
    Makes technical roles approachable and exciting
    """
    try:
        agent = JDGeneratorAgent()
        explanation = await agent.explain_to_candidate(
            jd_content=request.jd_content,
            role=request.role
        )
        return ExplainJDResponse(
            explanation=explanation,
            role=request.role
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to explain JD: {str(e)}")


@router.post("/rewrite-jd", response_model=RewriteJDResponse)
async def rewrite_jd_for_manager(
    request: RewriteJDRequest,
    current_user: User = Depends(require_permission("jobs.generate_jd"))
):
    """
    Rewrite JD as internal hiring manager briefing
    Focuses on team fit, success metrics, and interview guidance
    """
    try:
        agent = JDGeneratorAgent()
        briefing = await agent.rewrite_for_manager(
            jd_content=request.jd_content,
            role=request.role
        )
        return RewriteJDResponse(
            manager_briefing=briefing,
            role=request.role
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rewrite JD: {str(e)}")


@router.get("/skills/autocomplete", response_model=SkillAutocompleteResponse)
async def autocomplete_skills(
    query: str,
    category: str = None,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user)
):
    """
    Autocomplete skill suggestions as user types
    
    Args:
    - query: Partial skill name (min 2 characters)
    - category: Optional filter by category
    - limit: Max results (default 10)
    """
    if len(query) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
    
    results = search_skills(query, category, limit)
    
    suggestions = [
        SkillSuggestion(
            skill=r["skill"],
            category=r["category"],
            popularity=r["popularity"],
            related_skills=r["related_skills"]
        )
        for r in results
    ]
    
    return SkillAutocompleteResponse(
        suggestions=suggestions,
        query=query
    )


@router.get("/skills/categories")
async def get_categories(
    current_user: User = Depends(get_current_active_user)
):
    """Get list of all skill categories"""
    return {"categories": get_skill_categories()}


@router.post("/match-profiles", response_model=ProfileMatchResponse)
async def match_profiles(
    request: ProfileMatchRequest,
    current_user: User = Depends(require_permission("jobs.matcher.use"))
):
    """
    Match candidate profiles to job description
    
    **Required Permission:** `jobs.matcher.use`
    **Allowed Roles:** HR, Recruiter, Hiring Manager
    """
    # TODO: Implement AI profile matching
    # from app.services.ai.profile_matcher import ProfileMatcherAgent
    # agent = ProfileMatcherAgent()
    # result = await agent.match(...)
    
    return {
        "matches": [
            {"candidate": "John Doe", "score": 85, "highlights": ["Python", "FastAPI"]},
            {"candidate": "Jane Smith", "score": 78, "highlights": ["React", "TypeScript"]}
        ],
        "total_candidates": len(request.resumes)
    }


@router.get("/")
async def list_jobs(
    current_user: User = Depends(get_current_active_user)
):
    """
    List all jobs
    
    **Required:** Authenticated user
    """
    # TODO: Implement job listing from database
    return {
        "jobs": [],
        "total": 0
    }


@router.get("/{job_id}")
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get specific job details
    
    **Required:** Authenticated user
    """
    # TODO: Implement get job by ID
    return {
        "id": job_id,
        "title": "Software Engineer",
        "status": "active"
    }


@router.post("/chat/interactive-builder", response_model=ChatBuilderResponse)
async def interactive_job_builder(
    request: ChatBuilderRequest,
    current_user: User = Depends(require_permission("jobs.generate_jd"))
):
    """
    Interactive conversational job builder
    
    AI assistant collects job requirements through natural conversation
    and extracts structured data.
    
    **Flow:**
    1. User sends message describing job requirements
    2. AI asks clarifying questions
    3. Extracts structured data incrementally
    4. Returns completion status
    5. When complete, provides summary for form auto-fill
    
    **Required Permission:** jobs.generate_jd
    """
    try:
        agent = JobBuilderChatAgent()
        
        # Convert Pydantic models to dicts for agent processing
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation_history
        ]
        
        current_data = request.current_data.model_dump() if request.current_data else None
        
        # Process message
        result = await agent.process_message(
            user_message=request.message,
            conversation_history=conversation_history,
            current_data=current_data
        )
        
        # Add summary if complete
        if result.get("is_complete"):
            result["summary"] = agent.generate_summary(result["extracted_data"])
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Chat builder error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

