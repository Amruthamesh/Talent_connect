"""
AI-powered conversational job builder assistant.
Extracts structured job data through natural conversation.
"""

import json
import re
from typing import Dict, List, Optional, Any
from app.config import settings
from app.utils.openai_client import openai_client

class JobBuilderChatAgent:
    """
    Conversational AI agent that helps HR professionals define job requirements
    through natural dialogue and extracts structured data.
    """
    
    REQUIRED_FIELDS = [
        "role",
        "seniority",
        "location",
        "must_have_skills",
        "joining_timeline",
        "salary_range"
    ]
    
    OPTIONAL_FIELDS = [
        "salary_range",
        "company_tone",
        "special_requirements",
        "additional_notes"
    ]
    
    FIELD_MINIMUMS = {
        "must_have_skills": 2
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

REQUIRED INFORMATION TO COLLECT (6 essential fields only):
1. Job Title/Role - the position being hired for
2. Seniority Level - Entry/Mid/Senior/Lead/Principal
3. Location - Office/Remote/Hybrid or specific location
4. Must-Have Skills - minimum 2 required technical/functional skills
5. Joining Timeline - when you need this person (ASAP, within 30 days, flexible, etc.)
6. Salary Range - compensation range or budget for the role

OPTIONAL INFORMATION (will be auto-generated if not provided):
- Department
- Responsibilities
- Preferred Skills
- Expectations
- Team Context
- Company Tone
- Special Requirements
- Additional Notes

Note: The AI generator will intelligently populate missing optional fields based on the role, seniority, and skills provided.

CONVERSATION GUIDELINES:
1. Start with a warm greeting and ask about the role
2. When user provides information, acknowledge it briefly and naturally
3. If information is vague, ask for specifics
4. Guide them gently through missing required fields ONE AT A TIME
5. Keep it conversational and efficient - only 6 fields needed!
6. **IMPORTANT**: When all 6 required fields are collected, say:
   "Perfect! I have everything I need: role, seniority, location, key skills, timeline, and budget. Our AI will automatically generate comprehensive details for responsibilities, team context, and other aspects. Ready to generate the job description?"
7. If user says "Yes" or confirms → Set is_complete=true
8. If user wants to add optional details → Collect them, then mark complete

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
  "reply": "Great! A senior backend engineer - that's an important role. What are the must-have technical skills you're looking for? For example, specific programming languages or frameworks?",
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
    "team_context": null,
    "joining_timeline": null,
    "special_requirements": null,
    "additional_notes": null
  },
  "missing_required": ["must_have_skills", "location", "joining_timeline", "salary_range"],
  "completion_percentage": 33,
  "next_question_focus": "must_have_skills"
}

User: "Python, FastAPI, and PostgreSQL"
Response:
{
  "reply": "Perfect! Python, FastAPI, and PostgreSQL - solid tech stack. Where will this position be based - remote, on-site, or hybrid?",
  "extracted_data": {
    "role": "Backend Engineer",
    "seniority": "Senior",
    "department": null,
    "location": null,
    "must_have_skills": ["Python", "FastAPI", "PostgreSQL"],
    "preferred_skills": [],
    "expectations": null,
    "company_tone": null,
    "salary_range": null,
    "responsibilities": [],
    "team_context": null,
    "joining_timeline": null,
    "special_requirements": null,
    "additional_notes": null
  },
  "missing_required": ["location", "joining_timeline", "salary_range"],
  "completion_percentage": 50,
  "next_question_focus": "location"
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
        
        # Use global OpenAI client with SSL configuration
        self.client = openai_client
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
        return value not in (None, "", [], "")
    
    def _generate_fallback_response(self, user_message: str, current_data: dict) -> dict:
        """Generate a fallback response when OpenAI API is unavailable."""
        # Simple pattern matching for common job description fields
        message_lower = user_message.lower()
        updated_data = current_data.copy()
        
        # Extract role information
        if any(word in message_lower for word in ['engineer', 'developer', 'programmer', 'architect']):
            if not updated_data.get('role'):
                updated_data['role'] = 'Software Engineer'
        elif any(word in message_lower for word in ['manager', 'lead', 'director']):
            if not updated_data.get('role'):
                updated_data['role'] = 'Manager'
        elif any(word in message_lower for word in ['analyst', 'data scientist']):
            if not updated_data.get('role'):
                updated_data['role'] = 'Data Analyst'
        
        # Extract seniority
        if any(word in message_lower for word in ['senior', 'sr']):
            if not updated_data.get('seniority'):
                updated_data['seniority'] = 'Senior'
        elif any(word in message_lower for word in ['junior', 'jr', 'entry']):
            if not updated_data.get('seniority'):
                updated_data['seniority'] = 'Junior'
        elif any(word in message_lower for word in ['mid', 'middle', 'intermediate']):
            if not updated_data.get('seniority'):
                updated_data['seniority'] = 'Mid-level'
        
        # Extract location information - this is the key fix!
        location_keywords = {
            'remote': 'Remote',
            'hybrid': 'Hybrid',
            'chennai': 'Chennai',
            'bangalore': 'Bangalore', 
            'mumbai': 'Mumbai',
            'delhi': 'Delhi',
            'pune': 'Pune',
            'hyderabad': 'Hyderabad',
            'office': 'Office-based',
            'onsite': 'On-site',
            'work from home': 'Remote',
            'wfh': 'Remote'
        }
        
        for keyword, location in location_keywords.items():
            if keyword in message_lower:
                updated_data['location'] = location
                break
        
        # If it's a simple city name or location response, capture it directly
        if not updated_data.get('location'):
            # Check if the message is likely just a location name
            words = user_message.strip().split()
            if len(words) <= 3:  # Short responses likely to be location names
                updated_data['location'] = user_message.strip().title()
        
        # Extract skills mentioned
        common_skills = ['python', 'javascript', 'react', 'java', 'aws', 'docker', 'kubernetes', 'sql', 'nodejs', 'angular', 'vue']
        mentioned_skills = [skill for skill in common_skills if skill in message_lower]
        if mentioned_skills and not updated_data.get('must_have_skills'):
            updated_data['must_have_skills'] = mentioned_skills
        
        missing_required = self._get_missing_required(updated_data)
        completion_percentage = self._calculate_completion(updated_data)
        
        # Check if we just updated location and acknowledge it
        location_just_set = current_data.get('location') != updated_data.get('location') and updated_data.get('location')
        
        # Generate appropriate response based on what's missing
        if not updated_data.get('role'):
            reply = "I'd be happy to help you create a job description! Let's start with the basics - what role are you hiring for? For example, 'Software Engineer', 'Marketing Manager', or 'Data Scientist'?"
        elif not updated_data.get('seniority'):
            reply = f"Great! You're hiring for a {updated_data['role']}. What experience level are you looking for - Junior, Mid-level, Senior, or Lead?"
        elif not updated_data.get('must_have_skills') or len(updated_data.get('must_have_skills', [])) == 0:
            reply = f"Perfect! For the {updated_data.get('seniority', '')} {updated_data['role']} position, what are the key technical skills or qualifications that are absolutely required?"
        elif location_just_set:
            reply = f"Great! I've noted the location as {updated_data['location']}. Now, what are some responsibilities this person would have in this role?"
        elif not updated_data.get('location'):
            reply = "What's the location for this role? Is it remote, hybrid, or in a specific office location?"
        elif not updated_data.get('responsibilities') or len(updated_data.get('responsibilities', [])) == 0:
            reply = "What would be the main responsibilities and duties for this position? Please describe what this person would do day-to-day."
        elif not updated_data.get('department'):
            reply = "Which department or team will this role be part of?"
        else:
            reply = "Thanks for the information! I'm collecting the details for your job description. What other requirements or details would you like to add?"
        
        return {
            "reply": reply,
            "extracted_data": updated_data,
            "missing_required": missing_required,
            "completion_percentage": completion_percentage,
            "is_complete": len(missing_required) == 0,
            "next_question_focus": missing_required[0] if missing_required else None,
            "error": "API temporarily unavailable - using fallback mode"
        }
