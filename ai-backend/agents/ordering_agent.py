from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import Tool
from typing import List, Dict, Optional
import logging

from core.config import settings
from agents.medicine_parser import MedicineParser

logger = logging.getLogger(__name__)


class OrderingAgent:
    """AI Agent for handling customer ordering conversations"""
    
    def __init__(self):
        # Use rule-based parser (works without OpenAI)
        self.parser = MedicineParser()
        
        # Optional: Initialize LLM only if API key is available
        self.use_llm = False
        try:
            if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 20:
                self.llm = ChatOpenAI(
                    model=settings.AGENT_MODEL,
                    temperature=settings.AGENT_TEMPERATURE,
                    max_tokens=settings.AGENT_MAX_TOKENS,
                    api_key=settings.OPENAI_API_KEY
                )
                self.use_llm = True
                logger.info("LLM initialized successfully")
        except Exception as e:
            logger.warning(f"LLM not available, using rule-based parser: {str(e)}")
            self.use_llm = False
        
        self.system_prompt = """You are a helpful pharmacy assistant for Mediloon Pharmacy.
Your role is to help customers order medicines through natural conversation.

Key responsibilities:
1. Understand medicine requests from customer messages (voice or text)
2. Parse medicine names, dosages, and quantities accurately
3. Ask clarifying questions when needed
4. Suggest alternatives if requested medicine is unavailable
5. Inform about prescription requirements
6. Confirm orders before finalizing

Important guidelines:
- Be friendly, professional, and patient-focused
- Always verify dosage and quantity
- Warn about prescription requirements
- Suggest generics if available to save cost
- Handle multiple medicines in one order
- Support multiple languages (English, German, Arabic)

Current language: {language}

When a customer mentions a medicine, extract:
- Medicine name
- Dosage (if mentioned)
- Quantity (if mentioned, default to common pack sizes)
- Form (tablet, syrup, etc.)

Always confirm the complete order before proceeding to checkout.
"""
    
    async def process_message(
        self,
        message: str,
        conversation_history: List[Dict],
        user_context: Dict,
        language: str = "en"
    ) -> Dict:
        """
        Process a customer message and generate response
        
        Args:
            message: Customer's message
            conversation_history: Previous conversation messages
            user_context: User information and preferences
            language: Language code (en, de, ar)
        
        Returns:
            Dict with response message and parsed data
        """
        try:
            # Use rule-based parser (always works)
            parsed_data = self.parser.parse_message(message)
            
            logger.info(f"Parsed {len(parsed_data.get('medicines', []))} medicines from: {message[:50]}...")
            
            return {
                "message": parsed_data.get("response", "I've processed your request."),
                "parsed_medicines": parsed_data.get("medicines", []),
                "requires_clarification": parsed_data.get("requires_clarification", False),
                "next_action": parsed_data.get("next_action", "continue"),
                "confidence": parsed_data.get("confidence", 0.7)
            }
            
        except Exception as e:
            logger.error(f"Error in ordering agent: {str(e)}", exc_info=True)
            return {
                "message": "I apologize, but I'm having trouble processing your request. Could you please try again?",
                "parsed_medicines": [],
                "requires_clarification": True,
                "next_action": "retry",
                "confidence": 0.0
            }
    
    async def _parse_medicine_request(self, user_message: str, agent_response: str) -> Dict:
        """
        Parse medicine information from user message and agent response
        """
        # Use LLM to extract structured data
        extraction_prompt = f"""Extract medicine information from this conversation:

User: {user_message}
Assistant: {agent_response}

Extract the following in JSON format:
{{
    "medicines": [
        {{
            "name": "medicine name",
            "dosage": "dosage amount (e.g., 500mg)",
            "quantity": number,
            "form": "tablet/syrup/etc",
            "confidence": 0.0-1.0
        }}
    ],
    "requires_clarification": true/false,
    "next_action": "confirm/ask_details/add_to_cart/complete",
    "confidence": 0.0-1.0
}}

If no medicines are mentioned or unclear, return empty medicines list and requires_clarification: true.
"""
        
        try:
            extraction_response = await self.llm.ainvoke([
                SystemMessage(content="You are a data extraction assistant. Always respond with valid JSON."),
                HumanMessage(content=extraction_prompt)
            ])
            
            # Parse JSON from response
            import json
            response_text = extraction_response.content.strip()
            
            # Extract JSON if wrapped in code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            parsed = json.loads(response_text)
            return parsed
            
        except Exception as e:
            logger.error(f"Error parsing medicine request: {str(e)}")
            return {
                "medicines": [],
                "requires_clarification": True,
                "next_action": "retry",
                "confidence": 0.0
            }
    
    async def confirm_order(self, medicines: List[Dict], user_context: Dict) -> str:
        """Generate order confirmation message"""
        if not medicines:
            return "Your cart is empty. Please add medicines to proceed with checkout."
        
        response = f"Thank you, {user_context.get('name', 'Customer')}! Here's your order summary:\n\n"
        
        total_items = sum(med.get('quantity', 1) for med in medicines)
        
        for i, med in enumerate(medicines, 1):
            response += f"{i}. {med['medicine_name']} "
            if med.get('dosage'):
                response += f"{med['dosage']} "
            response += f"× {med['quantity']} = ${med.get('total_price', med.get('unit_price', 10.0) * med['quantity']):.2f}\n"
        
        response += f"\nTotal Items: {total_items}\n"
        response += "Status: Ready for delivery\n"
        response += "Estimated delivery: 2-3 business days\n\n"
        response += "Would you like to confirm this order?"
        
        return response
