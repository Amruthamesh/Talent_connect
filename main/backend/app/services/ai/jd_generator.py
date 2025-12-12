from typing import Optional, Literal
from app.config import settings
from app.utils.openai_client import openai_client
import json


CompanyTone = Literal["formal", "startup", "mnc", "tech"]


class JDGeneratorAgent:
    """
    Advanced AI Agent for generating job descriptions using OpenAI GPT models
    Behaves like an L4 HR analyst with deep expertise
    """
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        
        # Use global OpenAI client with SSL configuration
        self.client = openai_client
        self.model = "gpt-4o-mini"
    
    async def generate_jd(
        self,
        role: str,
        seniority: str,
        expectations: str,
        must_have_skills: list[str],
        preferred_skills: list[str],
        company_tone: CompanyTone = "formal",
        department: Optional[str] = None,
        location: Optional[str] = None
    ) -> dict:
        """
        Generate comprehensive job description with skill matrix and insights
        
        Args:
            role: Job title/role name
            seniority: Experience level (Entry/Mid/Senior/Lead/Principal)
            expectations: What success looks like in this role
            must_have_skills: Required technical & soft skills
            preferred_skills: Nice-to-have skills
            company_tone: Writing style (formal/startup/mnc/tech)
            department: Optional department name
            location: Optional location for salary benchmarking
        
        Returns:
            Dictionary with:
            - jd_content: Formatted job description
            - skill_matrix: Categorized skills with proficiency levels
            - salary_benchmark: Estimated salary range
            - metadata: Generation details
        """
        
        prompt = self._build_comprehensive_prompt(
            role, seniority, expectations, must_have_skills, 
            preferred_skills, company_tone, department, location
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": "You are an expert HR analyst who crafts comprehensive job descriptions."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = self._extract_content(response.choices[0].message)
            
            # Parse structured output
            parsed_output = self._parse_jd_response(content)
            
            return {
                **parsed_output,
                "metadata": {
                    "role": role,
                    "seniority": seniority,
                    "department": department,
                    "location": location,
                    "company_tone": company_tone,
                    "model": self.model,
                    "tokens_used": (response.usage.prompt_tokens or 0) + (response.usage.completion_tokens or 0)
                }
            }
            
        except Exception as e:
            raise Exception(f"Failed to generate job description: {str(e)}")
    
    
    def _build_comprehensive_prompt(
        self,
        role: str,
        seniority: str,
        expectations: str,
        must_have_skills: list[str],
        preferred_skills: list[str],
        company_tone: CompanyTone,
        department: Optional[str],
        location: Optional[str]
    ) -> str:
        """Build advanced L4 HR analyst prompt with structured output"""
        
        must_have_text = ", ".join(must_have_skills)
        preferred_text = ", ".join(preferred_skills)
        dept_text = f" in the {department} department" if department else ""
        location_text = f" (Location: {location})" if location else ""
        
        tone_guide = {
            "formal": "Professional, corporate, traditional language. Use formal titles and structured format.",
            "startup": "Dynamic, energetic, casual yet professional. Emphasize innovation, fast pace, and impact.",
            "mnc": "Global, structured, process-oriented. Emphasize scale, international exposure, and career growth.",
            "tech": "Technical, modern, collaborative. Use industry jargon appropriately, emphasize tech stack and engineering culture."
        }
        
        return f"""You are an L4 HR analyst with 10+ years of experience in talent acquisition and job design. You deeply understand role requirements, market standards, and what attracts top talent.

**TASK:** Generate a comprehensive, structured job description with supporting analysis.

**INPUTS:**
- **Role:** {role}{dept_text}{location_text}
- **Seniority Level:** {seniority}
- **Success Expectations:** {expectations}
- **Must-Have Skills:** {must_have_text}
- **Preferred Skills:** {preferred_text}
- **Company Tone:** {company_tone} - {tone_guide.get(company_tone, '')}

**OUTPUT FORMAT:** Provide your response as a JSON object with the following structure:

```json
{{
  "jd_content": {{
    "title": "Full job title",
    "overview": "2-3 sentence compelling overview",
    "responsibilities": ["Responsibility 1", "Responsibility 2", "..."],
    "required_qualifications": {{
      "education": ["Education requirements"],
      "experience": "X+ years experience description",
      "technical_skills": ["Skill 1", "Skill 2", "..."],
      "soft_skills": ["Skill 1", "Skill 2", "..."]
    }},
    "preferred_qualifications": ["Preferred 1", "Preferred 2", "..."],
    "what_we_offer": ["Benefit 1", "Benefit 2", "..."]
  }},
  "skill_matrix": {{
    "technical_skills": [
      {{"skill": "Skill Name", "category": "Frontend/Backend/DevOps/etc", "proficiency": "Expert/Advanced/Intermediate", "priority": "Must-Have/Preferred"}}
    ],
    "soft_skills": [
      {{"skill": "Skill Name", "importance": "Critical/High/Medium", "context": "Why it matters for this role"}}
    ]
  }},
  "salary_benchmark": {{
    "currency": "USD",
    "min": 80000,
    "max": 120000,
    "median": 100000,
    "note": "Based on {seniority} level, market standards, and required skills. Actual may vary by location and experience.",
    "factors": ["Factor 1 affecting salary", "Factor 2", "..."]
  }},
  "insights": {{
    "market_demand": "High/Medium/Low demand for this role",
    "key_differentiators": ["What makes this role unique"],
    "candidate_persona": "Profile of ideal candidate",
    "retention_factors": ["What will keep good people in this role"]
  }}
}}
```

**REQUIREMENTS:**
1. Write in the specified company tone ({company_tone})
2. Ensure all must-have skills are prominently featured
3. Make responsibilities specific and measurable where possible
4. Salary benchmark should be realistic for the seniority level and skills
5. Skill matrix should categorize skills logically
6. Insights should provide strategic hiring guidance
7. Avoid bias - focus on skills and experience, not demographics
8. Make it compelling for top talent

Generate the complete JSON response now:"""
    
    def _extract_content(self, message) -> str:
        """Normalize OpenAI response message content into a string."""
        content = getattr(message, "content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    parts.append(part.get("text", ""))
                elif hasattr(part, "type") and getattr(part, "type") == "text":
                    parts.append(getattr(part, "text", ""))
            return "\n".join(parts)
        return str(content)
    
    def _parse_jd_response(self, content: str) -> dict:
        """Parse the model's JSON response"""
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()
            
            parsed = json.loads(content)
            return parsed
        except Exception as e:
            # Fallback: return raw content if JSON parsing fails
            return {
                "jd_content": {"overview": content},
                "skill_matrix": {"technical_skills": [], "soft_skills": []},
                "salary_benchmark": {},
                "insights": {}
            }
    
    async def explain_to_candidate(self, jd_content: dict, role: str) -> str:
        """
        Translate technical JD into candidate-friendly explanation
        Perfect for "Explain this JD to a candidate" button
        """
        prompt = f"""You are a friendly career counselor explaining a job opportunity.

Take this job description for **{role}** and rewrite it in a warm, conversational tone that:
1. Explains what they'll actually DO day-to-day
2. Translates technical jargon into plain English
3. Highlights growth opportunities
4. Makes it feel approachable and exciting
5. Addresses common candidate concerns

Original JD:
{json.dumps(jd_content, indent=2)}

Write a friendly, engaging explanation (300-400 words) that would help a candidate understand if this role is right for them."""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.8,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Failed to explain JD: {str(e)}")
    
    async def rewrite_for_manager(self, jd_content: dict, role: str) -> str:
        """
        Rewrite JD in internal manager-speak with focus on team fit and success metrics
        Perfect for "Rewrite this JD internally for a manager" button
        """
        prompt = f"""You are an internal talent partner translating a candidate-facing JD into a hiring manager briefing.

For the **{role}** position, create an internal document that:
1. Focuses on team composition and gaps this hire fills
2. Specifies success metrics for first 30/60/90 days
3. Highlights integration challenges
4. Defines collaboration touchpoints with other teams
5. Notes red flags to watch for in interviews
6. Suggests interview focus areas

Original JD:
{json.dumps(jd_content, indent=2)}

Write a crisp, actionable manager briefing (400-500 words) with clear structure and bullet points."""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1800,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Failed to rewrite JD: {str(e)}")
