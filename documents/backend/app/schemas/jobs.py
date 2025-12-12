from pydantic import BaseModel, Field
from typing import List, Optional, Literal


# Request Models
class GenerateJDRequest(BaseModel):
    """Request for generating job description"""
    role: str = Field(..., description="Job title/role name", example="Senior Full-Stack Engineer")
    seniority: str = Field(..., description="Experience level", example="Senior")
    expectations: str = Field(..., description="What success looks like", example="Build scalable features, mentor juniors, drive technical decisions")
    must_have_skills: List[str] = Field(..., description="Required skills", example=["React", "Node.js", "PostgreSQL", "AWS"])
    preferred_skills: List[str] = Field(default=[], description="Nice-to-have skills", example=["TypeScript", "Docker", "GraphQL"])
    company_tone: Literal["formal", "startup", "mnc", "tech"] = Field(default="formal", description="Writing style")
    department: Optional[str] = Field(None, description="Department name", example="Engineering")
    location: Optional[str] = Field(None, description="Job location", example="San Francisco, CA")


class ExplainJDRequest(BaseModel):
    """Request for explaining JD to candidates"""
    jd_content: dict = Field(..., description="Generated JD content")
    role: str = Field(..., description="Job title")


class RewriteJDRequest(BaseModel):
    """Request for rewriting JD for managers"""
    jd_content: dict = Field(..., description="Generated JD content")
    role: str = Field(..., description="Job title")


# Response Models
class JDContent(BaseModel):
    """Structured job description content"""
    title: str
    overview: str
    responsibilities: List[str]
    required_qualifications: dict
    preferred_qualifications: List[str]
    what_we_offer: List[str]


class SkillItem(BaseModel):
    """Individual skill in matrix"""
    skill: str
    category: str
    proficiency: str
    priority: str


class SoftSkillItem(BaseModel):
    """Soft skill with context"""
    skill: str
    importance: str
    context: str


class SkillMatrix(BaseModel):
    """Categorized skills with proficiency"""
    technical_skills: List[SkillItem]
    soft_skills: List[SoftSkillItem]


class SalaryBenchmark(BaseModel):
    """Salary range estimation"""
    currency: str = "USD"
    min: int
    max: int
    median: int
    note: str
    factors: List[str]


class JDInsights(BaseModel):
    """Strategic insights for hiring"""
    market_demand: str
    key_differentiators: List[str]
    candidate_persona: str
    retention_factors: List[str]


class GenerateJDResponse(BaseModel):
    """Complete JD generation response"""
    jd_content: JDContent
    skill_matrix: SkillMatrix
    salary_benchmark: SalaryBenchmark
    insights: JDInsights
    metadata: dict


class ExplainJDResponse(BaseModel):
    """Candidate-friendly explanation"""
    explanation: str
    role: str


class RewriteJDResponse(BaseModel):
    """Manager-focused briefing"""
    manager_briefing: str
    role: str


# Autocomplete Models
class SkillAutocompleteRequest(BaseModel):
    """Request for skill autocomplete"""
    query: str = Field(..., description="Partial skill name", min_length=2)
    category: Optional[str] = Field(None, description="Filter by category")
    limit: int = Field(10, description="Max results", ge=1, le=50)


class SkillSuggestion(BaseModel):
    """Skill autocomplete suggestion"""
    skill: str
    category: str
    popularity: int  # How common this skill is
    related_skills: List[str]


class SkillAutocompleteResponse(BaseModel):
    """Autocomplete results"""
    suggestions: List[SkillSuggestion]
    query: str


# Chat Builder Models
class ChatMessage(BaseModel):
    """Individual chat message"""
    role: Literal["user", "assistant"]
    content: str


class ExtractedJobData(BaseModel):
    """Structured job data extracted from conversation"""
    role: Optional[str] = None
    seniority: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    must_have_skills: List[str] = []
    preferred_skills: List[str] = []
    responsibilities: List[str] = []
    expectations: Optional[str] = None
    team_context: Optional[str] = None
    joining_timeline: Optional[str] = None
    company_tone: Optional[str] = None
    salary_range: Optional[str] = None
    special_requirements: Optional[str] = None
    additional_notes: Optional[str] = None


class ChatBuilderRequest(BaseModel):
    """Request for interactive job builder chat"""
    message: str = Field(..., description="User's message", min_length=1)
    conversation_history: List[ChatMessage] = Field(default=[], description="Previous messages")
    current_data: Optional[ExtractedJobData] = Field(None, description="Currently extracted data")


class ChatBuilderResponse(BaseModel):
    """Response from chat builder"""
    reply: str = Field(..., description="AI assistant's response")
    extracted_data: ExtractedJobData = Field(..., description="Extracted/updated job data")
    missing_required: List[str] = Field(..., description="List of missing required fields")
    completion_percentage: int = Field(..., description="0-100 completion status", ge=0, le=100)
    is_complete: bool = Field(..., description="Whether all required fields are collected")
    next_question_focus: Optional[str] = Field(None, description="Next field to ask about")
    summary: Optional[str] = Field(None, description="Human-readable summary when complete")
