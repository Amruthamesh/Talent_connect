"""
Document Chat Service - AI-powered conversational document generation
"""
from openai import OpenAI
from typing import List, Dict, Any
from app.config import settings
import json


class DocumentChatService:
    """
    AI-powered chat service for document generation
    Provides natural conversation for creating HR documents
    """
    
    def __init__(self):
        """Initialize the chat service with OpenAI API."""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"
    
    def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        available_templates: List[Dict[str, Any]],
        session_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate an intelligent response based on conversation context
        
        Args:
            user_message: The user's latest message
            conversation_history: Previous messages in the conversation
            available_templates: List of document templates available
            session_context: Current session state (selected template, collected data, etc.)
        
        Returns:
            Dictionary with reply, action, and metadata
        """
        
        # Build system prompt with context
        template_list = "\n".join([f"- {t['name']}: {t.get('description', '')}" for t in available_templates])
        
        system_prompt = f"""You are an AI assistant for DHL's HR Document Generator. Your role is to help users create professional HR documents through natural conversation.

Available document types:
{template_list}

Your responsibilities:
1. Understand what document the user needs
2. Guide them through providing required information
3. Ask clarifying questions when needed
4. Be friendly, professional, and efficient
5. Suggest the most appropriate document type
6. Extract information from natural language

Current context: {json.dumps(session_context or {}, indent=2)}

Guidelines:
- Keep responses concise and clear
- Ask one question at a time when collecting information
- Confirm understanding before proceeding
- Use bullet points for lists
- Avoid technical jargon
- Be helpful and proactive"""

        # Build conversation for API
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in conversation_history[-10:]:  # Last 10 messages for context
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            reply = response.choices[0].message.content.strip()
            
            # Analyze reply for actions
            action = self._detect_action(user_message, reply, available_templates)
            
            return {
                "reply": reply,
                "action": action.get("type"),
                "action_data": action.get("data"),
                "is_complete": False
            }
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fallback response
            return {
                "reply": f"I can help you create: {', '.join([t['name'] for t in available_templates])}. Which document do you need?",
                "action": None,
                "action_data": None,
                "is_complete": False
            }
    
    def _detect_action(
        self,
        user_message: str,
        ai_reply: str,
        available_templates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect if an action should be taken based on the conversation
        
        Returns:
            Dictionary with action type and data
        """
        user_lower = user_message.lower()
        
        # Check for template selection
        for template in available_templates:
            template_name_lower = template['name'].lower()
            if template_name_lower in user_lower or any(word in user_lower for word in template_name_lower.split()):
                return {
                    "type": "template_selected",
                    "data": {"template_id": template['id'], "template_name": template['name']}
                }
        
        # Check for method selection
        if any(word in user_lower for word in ['manual', 'type', 'fill', 'guide']):
            return {
                "type": "method_selected",
                "data": {"method": "manual_entry"}
            }
        
        if any(word in user_lower for word in ['csv', 'upload', 'file']):
            return {
                "type": "method_selected",
                "data": {"method": "upload_csv"}
            }
        
        if any(word in user_lower for word in ['download', 'template']):
            return {
                "type": "method_selected",
                "data": {"method": "download_template"}
            }
        
        return {"type": None, "data": None}
