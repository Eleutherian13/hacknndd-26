from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import List, Dict, Optional
import logging

from core.config import settings

logger = logging.getLogger(__name__)


class SafetyAgent:
    """AI Agent for prescription validation and drug interaction checking"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.AGENT_MODEL,
            temperature=0.2,  # Low temperature for consistent safety checks
            api_key=settings.OPENAI_API_KEY
        )
    
    async def check_prescription_requirement(
        self,
        medicine_name: str,
        medicine_data: Dict
    ) -> Dict:
        """
        Check if a medicine requires prescription
        
        Args:
            medicine_name: Name of the medicine
            medicine_data: Medicine details from database
        
        Returns:
            Dict with prescription requirement status
        """
        try:
            requires_prescription = medicine_data.get('prescription_required', 'no') == 'yes'
            
            return {
                "medicine_name": medicine_name,
                "requires_prescription": requires_prescription,
                "reason": "Controlled substance" if requires_prescription else "Over-the-counter",
                "action_required": "upload_prescription" if requires_prescription else "none"
            }
            
        except Exception as e:
            logger.error(f"Error checking prescription requirement: {str(e)}")
            return {
                "medicine_name": medicine_name,
                "requires_prescription": True,  # Default to safe side
                "reason": "Unable to verify",
                "action_required": "contact_pharmacist"
            }
    
    async def check_drug_interactions(
        self,
        new_medicines: List[Dict],
        existing_medications: List[Dict]
    ) -> Dict:
        """
        Check for potential drug interactions
        
        Args:
            new_medicines: Medicines being ordered
            existing_medications: User's current medications
        
        Returns:
            Dict with interaction warnings
        """
        try:
            # Prepare medicine lists
            new_med_names = [m.get('name', m.get('medicine_name', '')) for m in new_medicines]
            existing_med_names = [m.get('name', m.get('medicine_name', '')) for m in existing_medications]
            
            if not existing_med_names:
                return {
                    "has_interactions": False,
                    "warnings": [],
                    "safe_to_proceed": True
                }
            
            # Use LLM to check interactions
            prompt = f"""As a pharmaceutical safety expert, check for drug interactions:

New medicines being ordered:
{', '.join(new_med_names)}

Current medications:
{', '.join(existing_med_names)}

Analyze potential interactions and provide:
1. Any critical interactions (contraindicated)
2. Moderate interactions (caution advised)
3. Minor interactions (monitor)

Respond in JSON format:
{{
    "has_interactions": true/false,
    "critical_interactions": [
        {{"medicine1": "name", "medicine2": "name", "severity": "critical", "description": "explanation"}}
    ],
    "moderate_interactions": [...],
    "minor_interactions": [...],
    "recommendation": "overall safety recommendation"
}}
"""
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a pharmaceutical safety expert. Always respond with valid JSON."),
                HumanMessage(content=prompt)
            ])
            
            # Parse response
            import json
            response_text = response.content.strip()
            
            # Extract JSON if wrapped in code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            interaction_data = json.loads(response_text)
            
            # Determine if safe to proceed
            has_critical = len(interaction_data.get('critical_interactions', [])) > 0
            safe_to_proceed = not has_critical
            
            warnings = []
            
            # Format warnings
            for interaction in interaction_data.get('critical_interactions', []):
                warnings.append({
                    "severity": "critical",
                    "message": f"CRITICAL: {interaction['medicine1']} and {interaction['medicine2']} - {interaction['description']}",
                    "action": "DO NOT PROCEED - Consult pharmacist"
                })
            
            for interaction in interaction_data.get('moderate_interactions', []):
                warnings.append({
                    "severity": "moderate",
                    "message": f"CAUTION: {interaction['medicine1']} and {interaction['medicine2']} - {interaction['description']}",
                    "action": "Consult pharmacist before use"
                })
            
            logger.info(f"Drug interaction check: {len(warnings)} warnings found")
            
            return {
                "has_interactions": interaction_data.get('has_interactions', False),
                "warnings": warnings,
                "safe_to_proceed": safe_to_proceed,
                "recommendation": interaction_data.get('recommendation', ''),
                "requires_pharmacist_review": has_critical
            }
            
        except Exception as e:
            logger.error(f"Error checking drug interactions: {str(e)}", exc_info=True)
            # Default to requiring review on error
            return {
                "has_interactions": True,
                "warnings": [{
                    "severity": "critical",
                    "message": "Unable to verify drug interactions",
                    "action": "Consult pharmacist before proceeding"
                }],
                "safe_to_proceed": False,
                "requires_pharmacist_review": True
            }
    
    async def validate_dosage(
        self,
        medicine_name: str,
        requested_dosage: str,
        standard_dosages: List[str]
    ) -> Dict:
        """
        Validate if requested dosage is appropriate
        
        Args:
            medicine_name: Name of medicine
            requested_dosage: Dosage requested by user
            standard_dosages: List of standard dosages available
        
        Returns:
            Dict with validation result
        """
        try:
            is_valid = requested_dosage in standard_dosages
            
            if is_valid:
                return {
                    "is_valid": True,
                    "medicine_name": medicine_name,
                    "requested_dosage": requested_dosage,
                    "message": "Dosage is appropriate"
                }
            else:
                # Find closest match
                closest_match = self._find_closest_dosage(requested_dosage, standard_dosages)
                
                return {
                    "is_valid": False,
                    "medicine_name": medicine_name,
                    "requested_dosage": requested_dosage,
                    "message": f"Dosage not available. Did you mean {closest_match}?",
                    "suggested_dosage": closest_match,
                    "available_dosages": standard_dosages
                }
                
        except Exception as e:
            logger.error(f"Error validating dosage: {str(e)}")
            return {
                "is_valid": False,
                "message": "Unable to validate dosage",
                "action": "Contact pharmacist"
            }
    
    def _find_closest_dosage(self, requested: str, available: List[str]) -> str:
        """Find closest matching dosage from available options"""
        if not available:
            return requested
        
        # Simple string matching - in production, use more sophisticated matching
        requested_lower = requested.lower()
        
        for dosage in available:
            if dosage.lower() in requested_lower or requested_lower in dosage.lower():
                return dosage
        
        # Return first available if no match
        return available[0]
    
    async def comprehensive_safety_check(
        self,
        order_items: List[Dict],
        user_profile: Dict
    ) -> Dict:
        """
        Perform comprehensive safety check for an order
        
        Args:
            order_items: Items in the order
            user_profile: User profile with medical history
        
        Returns:
            Comprehensive safety report
        """
        try:
            checks = {
                "prescription_checks": [],
                "interaction_checks": None,
                "dosage_checks": [],
                "allergy_checks": [],
                "overall_safe": True,
                "requires_review": False,
                "warnings": []
            }
            
            # Check prescriptions for each item
            for item in order_items:
                prescription_check = await self.check_prescription_requirement(
                    item.get('medicine_name', ''),
                    item
                )
                checks["prescription_checks"].append(prescription_check)
                
                if prescription_check.get('requires_prescription'):
                    checks["requires_review"] = True
            
            # Check drug interactions
            existing_meds = user_profile.get('current_medications', [])
            if existing_meds:
                interaction_check = await self.check_drug_interactions(
                    order_items,
                    existing_meds
                )
                checks["interaction_checks"] = interaction_check
                
                if not interaction_check.get('safe_to_proceed'):
                    checks["overall_safe"] = False
                    checks["requires_review"] = True
            
            # Check allergies
            user_allergies = user_profile.get('allergies', [])
            if user_allergies:
                for item in order_items:
                    ingredients = item.get('active_ingredients', [])
                    for allergy in user_allergies:
                        for ingredient in ingredients:
                            if allergy.lower() in ingredient.lower():
                                checks["allergy_checks"].append({
                                    "medicine": item.get('medicine_name'),
                                    "allergen": allergy,
                                    "severity": "critical"
                                })
                                checks["overall_safe"] = False
                                checks["requires_review"] = True
            
            logger.info(f"Safety check complete: safe={checks['overall_safe']}, review={checks['requires_review']}")
            
            return checks
            
        except Exception as e:
            logger.error(f"Error in comprehensive safety check: {str(e)}")
            return {
                "overall_safe": False,
                "requires_review": True,
                "error": str(e)
            }
