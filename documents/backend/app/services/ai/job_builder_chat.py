"""
AI-powered conversational job builder assistant.
Extracts structured job data through natural conversation.
"""

from openai import OpenAI
import json
import re
from typing import Dict, List, Optional, Any
from app.config import settings

class JobBuilderChatAgent:
    """
    Conversational AI agent that helps HR professionals define job requirements
    through natural dialogue and extracts structured data.
    """
    
    REQUIRED_FIELDS = [
        "role",
        "seniority",
        "department",
        "responsibilities",
        "must_have_skills",
        "preferred_skills",
        "expectations",
        "location",
        "team_context",
        "joining_timeline"
    ]
    
    OPTIONAL_FIELDS = [
        "salary_range",
        "company_tone",
        "special_requirements",
        "additional_notes"
    ]
    
    FIELD_MINIMUMS = {
        "must_have_skills": 1,
        "preferred_skills": 1,
        "responsibilities": 1
    }
    
    SYSTEM_PROMPT = """You are an expert HR assistant helping recruiters and hiring managers define job requirements through conversation.

YOUR ROLE:
- Extract structured job information from natural conversation
- Ask ONE clarifying question at a time (never multiple questions at once)
- Be conversational, friendly, and professional
- Remember context from the entire conversation
- Guide the user to provide complete information
- After collecting all required info, ask if they want to add anything else
- If the user deflects with phrases like "you decide" or "surprise me", treat it as a request for your expert recommendation: propose 2-3 thoughtful suggestions grounded in the role, industry norms, or similar positions, while inviting confirmation or edits.

REQUIRED INFORMATION TO COLLECT (11 fields):
1. Job Title/Role - the position being hired for
2. Seniority Level - Entry/Mid/Senior/Lead/Principal
3. Department - which team/department this role belongs to
4. Responsibilities - main duties and tasks (3-5 key points)
5. Must-Have Skills - minimum 3 required technical/functional skills
6. Nice-to-Have Skills - at least 2 preferred but not mandatory skills
7. Expectations - what success looks like in this role
8. Location - Office/Remote/Hybrid or specific location
9. Team Context - team size, reporting structure, who they'll work with
10. Joining Timeline - when you need this person (ASAP, within 30 days, flexible, etc.)

OPTIONAL INFORMATION:
- Salary Range
- Company Tone (Formal/Startup/MNC/Tech)
- Special Requirements
- Additional context

CONVERSATION GUIDELINES:
1. Start with a warm greeting and ask about the role
2. When user provides information, acknowledge it briefly and naturally
3. If information is vague, ask for specifics
4. Guide them gently through missing required fields ONE AT A TIME
5. Don't interrogate - keep it conversational
6. **IMPORTANT**: When all 10 required fields are collected, say:
   "Great! I've gathered all the essential information. Would you like to add any other details or special requirements?"
7. If user says "No" or "That's it" → Set is_complete=true and provide final summary
8. If user adds more info → Update data and ask again if they're done

EXTRACTION RULES:
- Extract seniority from context (Junior/Entry → "Entry", Senior → "Senior", Lead/Staff → "Lead", etc.)
- Convert skill mentions to skill arrays (must-have AND nice-to-have separately)
- Parse responsibilities into clear bullet points
- Extract team context (team size, reporting structure)
- Infer joining timeline from urgency cues

RESPONSE FORMAT:
You must respond with ONLY a JSON object in this exact format:
{
  "reply": "Your conversational response to the user",
  "extracted_data": {
    "role": "Job title or null",
    "seniority": "Entry/Mid/Senior/Lead/Principal or null",
    "department": "Department name or null",
    "location": "Location or null",
    "must_have_skills": ["skill1", "skill2", ...],
    "preferred_skills": ["skill1", ...],
    "responsibilities": ["resp1", "resp2", ...],
    "expectations": "Description of role expectations or null",
    "team_context": "Team details or null",
    "joining_timeline": "Timeline or null",
    "company_tone": "formal/startup/mnc/tech or null",
    "salary_range": "Range or null",
    "special_requirements": "Special requirements or null",
    "additional_notes": "Any extra context or null"
  },
  "missing_required": ["list of missing required field names"],
  "completion_percentage": 0-100,
  "next_question_focus": "Field name to ask about next or null"
}

IMPORTANT: Always output valid JSON. Do not include markdown code blocks or any text outside the JSON object.

EXAMPLES:

User: "I need to hire a senior backend engineer"
Response:
{
  "reply": "Great! A senior backend engineer - that's an important role. To help me understand the position better, what are the must-have technical skills you're looking for? For example, specific programming languages, frameworks, or technologies?",
  "extracted_data": {
    "role": "Backend Engineer",
    "seniority": "Senior",
    "department": null,
    "location": null,
    "must_have_skills": [],
    "preferred_skills": [],
    "expectations": null,
    "company_tone": null,
    "salary_range": null,
    "responsibilities": [],
    "additional_notes": null
  },
  "missing_required": ["must_have_skills", "expectations", "location"],
  "completion_percentage": 40,
  "next_question_focus": "must_have_skills"
}

User: "They need Python, FastAPI, and PostgreSQL. Should have 5+ years experience with microservices"
Response:
{
  "reply": "Perfect! Python, FastAPI, and PostgreSQL with microservices experience - solid tech stack. Now, what will this person be mainly responsible for? What are the key expectations or outcomes for this role?",
  "extracted_data": {
    "role": "Backend Engineer",
    "seniority": "Senior",
    "department": null,
    "location": null,
    "must_have_skills": ["Python", "FastAPI", "PostgreSQL", "Microservices"],
    "preferred_skills": [],
    "expectations": null,
    "company_tone": null,
    "salary_range": null,
    "responsibilities": [],
    "additional_notes": "5+ years experience required"
  },
  "missing_required": ["expectations", "location"],
  "completion_percentage": 60,
  "next_question_focus": "expectations"
}
"""

    LOW_INFORMATION_RESPONSES = {
        "you surprise me",
        "surprise me",
        "idk",
        "i don't know",
        "dont know",
        "not sure",
        "whatever you think",
        "anything",
        "up to you",
        "your choice"
    }
    
    def __init__(self):
        """Initialize the chat agent with OpenAI API."""
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
    
    async def process_message(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        current_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process user message and return AI response with extracted data.
        
        Args:
            user_message: Latest message from user
            conversation_history: Previous messages [{"role": "user/assistant", "content": "..."}]
            current_data: Currently extracted job data
            
        Returns:
            Dict containing reply, extracted_data, completion status, etc.
        """
        if current_data is None:
            current_data = self._initialize_data_structure()
        
        # Build conversation context
        messages = []
        
        # Add conversation history
        for msg in conversation_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Add context about current data if exists
        if self._has_any_data(current_data):
            context_prompt = f"\n\nCURRENT EXTRACTED DATA:\n{json.dumps(current_data, indent=2)}\n\nUse this context to avoid asking about information already provided."
            messages[-1]["content"] += context_prompt
        
        normalized_message = user_message.strip().lower()
        if self._is_low_information_response(normalized_message):
            focus_field = self._get_missing_required(current_data)
            focus_field = focus_field[0] if focus_field else "role"
            user_message = self._build_suggestion_prompt(
                focus_field,
                user_message,
                current_data
            )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    *messages
                ],
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            response_text = self._extract_content(response.choices[0].message)
            
            # Parse JSON response
            result = self._parse_response(response_text)
            
            # Merge extracted data with current data
            merged_data = self._merge_data(current_data, result.get("extracted_data", {}))
            result["extracted_data"] = merged_data
            
            # Calculate actual completion
            result["completion_percentage"] = self._calculate_completion(merged_data)
            result["missing_required"] = self._get_missing_required(merged_data)
            result["is_complete"] = len(result["missing_required"]) == 0
            
            return result
            
        except Exception as e:
            print(f"Error in chat agent: {e}")
            return {
                "reply": "I apologize, I'm having trouble processing that. Could you rephrase or provide more details?",
                "extracted_data": current_data,
                "missing_required": self._get_missing_required(current_data),
                "completion_percentage": self._calculate_completion(current_data),
                "is_complete": False,
                "error": str(e)
            }
    
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
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response, handling markdown code blocks."""
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "reply": response_text,
                "extracted_data": {},
                "missing_required": self.REQUIRED_FIELDS,
                "completion_percentage": 0,
                "next_question_focus": "role"
            }
    
    def _is_low_information_response(self, message: str) -> bool:
        clean = re.sub(r'[^\w\s]', '', message)
        return clean in self.LOW_INFORMATION_RESPONSES
    
    def _build_suggestion_prompt(self, field: str, original_message: str, current_data: Dict[str, Any]) -> str:
        context_bits = []
        if current_data.get("role"):
            context_bits.append(f"Role: {current_data['role']}")
        if current_data.get("department"):
            context_bits.append(f"Department: {current_data['department']}")
        if current_data.get("seniority"):
            context_bits.append(f"Seniority: {current_data['seniority']}")
        if context_bits:
            context_text = "Known context -> " + ", ".join(context_bits)
        else:
            context_text = "Limited context provided so far."
        
        return (
            f"The user responded with '{original_message}', indicating they'd like your expert recommendation "
            f"for the field '{field}'. {context_text} Provide 2-3 thoughtful, role-appropriate suggestions for "
            f"{field.replace('_', ' ')} and invite the user to confirm or adjust them. Maintain a friendly tone "
            f"and keep guiding the conversation."
        )
    
    def _initialize_data_structure(self) -> Dict[str, Any]:
        """Initialize empty data structure."""
        return {
            "role": None,
            "seniority": None,
            "department": None,
            "location": None,
            "must_have_skills": [],
            "preferred_skills": [],
            "responsibilities": [],
            "expectations": None,
            "team_context": None,
            "joining_timeline": None,
            "company_tone": None,
            "salary_range": None,
            "special_requirements": None,
            "additional_notes": None
        }
    
    def _has_any_data(self, data: Dict[str, Any]) -> bool:
        """Check if any data has been extracted."""
        for key, value in data.items():
            if value and value != [] and value != None:
                return True
        return False
    
    def _merge_data(self, current: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """Merge new extracted data with current data."""
        merged = current.copy()
        
        for key, value in new.items():
            if key in merged:
                if isinstance(value, list):
                    # For lists, combine and deduplicate
                    if value:
                        existing = merged[key] or []
                        merged[key] = list(set(existing + value))
                elif value is not None and value != "":
                    # For other values, prefer new data if not null
                    merged[key] = value
        
        return merged
    
    def _calculate_completion(self, data: Dict[str, Any]) -> int:
        """Calculate completion percentage based on required fields."""
        total = len(self.REQUIRED_FIELDS)
        completed = 0
        
        for field in self.REQUIRED_FIELDS:
            if self._has_required_value(field, data.get(field)):
                completed += 1
        
        return int((completed / total) * 100)
    
    def _get_missing_required(self, data: Dict[str, Any]) -> List[str]:
        """Get list of missing required fields."""
        missing = []
        
        for field in self.REQUIRED_FIELDS:
            if not self._has_required_value(field, data.get(field)):
                missing.append(field)
        
        return missing
    
    def generate_summary(self, data: Dict[str, Any]) -> str:
        """Generate a human-readable summary of collected data."""
        summary_parts = []
        
        if data.get("role"):
            seniority = data.get("seniority", "")
            summary_parts.append(f"**Role:** {seniority} {data['role']}" if seniority else f"**Role:** {data['role']}")
        
        if data.get("department"):
            summary_parts.append(f"**Department:** {data['department']}")
        
        if data.get("location"):
            summary_parts.append(f"**Location:** {data['location']}")
        
        if data.get("must_have_skills"):
            skills_str = ", ".join(data["must_have_skills"])
            summary_parts.append(f"**Must-Have Skills:** {skills_str}")
        
        if data.get("preferred_skills"):
            skills_str = ", ".join(data["preferred_skills"])
            summary_parts.append(f"**Preferred Skills:** {skills_str}")
        
        if data.get("expectations"):
            summary_parts.append(f"**Expectations:** {data['expectations']}")
        
        if data.get("salary_range"):
            summary_parts.append(f"**Salary Range:** {data['salary_range']}")
        
        if data.get("responsibilities"):
            resp_str = "\n  • " + "\n  • ".join(data["responsibilities"])
            summary_parts.append(f"**Key Responsibilities:**{resp_str}")
        
        return "\n\n".join(summary_parts)

    def _has_required_value(self, field: str, value: Any) -> bool:
        """Check whether a field meets its minimum data requirements."""
        if field in self.FIELD_MINIMUMS:
            min_count = self.FIELD_MINIMUMS[field]
            return bool(value) and isinstance(value, list) and len(value) >= min_count
        if isinstance(value, list):
            return bool(value)
        return value not in (None, "", [])
