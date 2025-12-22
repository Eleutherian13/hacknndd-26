"""
Rule-based medicine parser - works without OpenAI API
Parses medicine names, dosages, quantities from natural language
"""
import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Common medicine database
COMMON_MEDICINES = {
    'paracetamol': ['paracetamol', 'tylenol', 'acetaminophen', 'paracitamol'],
    'ibuprofen': ['ibuprofen', 'advil', 'motrin', 'brufen'],
    'aspirin': ['aspirin', 'aspirine', 'acetylsalicylic'],
    'amoxicillin': ['amoxicillin', 'amoxycillin', 'amoxy'],
    'metformin': ['metformin', 'glucophage'],
    'omeprazole': ['omeprazole', 'prilosec'],
    'lisinopril': ['lisinopril', 'prinivil', 'zestril'],
    'atorvastatin': ['atorvastatin', 'lipitor'],
    'amlodipine': ['amlodipine', 'norvasc'],
    'metoprolol': ['metoprolol', 'lopressor'],
    'losartan': ['losartan', 'cozaar'],
    'gabapentin': ['gabapentin', 'neurontin'],
    'hydrochlorothiazide': ['hydrochlorothiazide', 'hctz'],
    'sertraline': ['sertraline', 'zoloft'],
    'simvastatin': ['simvastatin', 'zocor'],
    'vitamin d': ['vitamin d', 'vit d', 'cholecalciferol'],
    'vitamin c': ['vitamin c', 'vit c', 'ascorbic acid'],
    'insulin': ['insulin', 'humalog', 'novolog'],
    'levothyroxine': ['levothyroxine', 'synthroid'],
    'clopidogrel': ['clopidogrel', 'plavix'],
}

class MedicineParser:
    """Parse medicine information from natural language"""
    
    def __init__(self):
        self.dosage_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(mg|g|ml|mcg|iu|units?)', re.IGNORECASE)
        self.quantity_pattern = re.compile(r'(\d+)\s*(tablet|capsule|pill|strip|bottle|pack|box|count|pieces?|tabs?|caps?)', re.IGNORECASE)
        self.simple_quantity = re.compile(r'\b(\d+)\s*(?:of|x|×)?\s*(?=tablet|capsule|pill|tab|cap)', re.IGNORECASE)
        
    def parse_message(self, message: str) -> Dict:
        """
        Parse user message to extract medicine information
        
        Returns:
            {
                "medicines": [
                    {
                        "name": "Medicine Name",
                        "dosage": "500mg",
                        "quantity": 30,
                        "form": "tablet",
                        "confidence": 0.85
                    }
                ],
                "requires_clarification": False,
                "next_action": "confirm",
                "confidence": 0.85
            }
        """
        message_lower = message.lower()
        medicines = []
        
        # Check if this is a greeting or non-medicine message
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
        if any(greet in message_lower for greet in greetings) and not any(med in message_lower for meds in COMMON_MEDICINES.values() for med in meds):
            return {
                "medicines": [],
                "requires_clarification": False,
                "next_action": "greet",
                "confidence": 1.0,
                "response": "Hello! I'm here to help you order medicines. You can tell me what medicine you need, like 'I need Paracetamol 500mg, 30 tablets' or 'I want Aspirin'."
            }
        
        # Split by common separators to handle multiple medicines
        segments = re.split(r'\band\b|\balso\b|,\s*(?=\w)', message)
        
        for segment in segments:
            segment = segment.strip()
            if len(segment) < 3:
                continue
                
            # Find medicine name
            medicine_name = self._extract_medicine_name(segment)
            if not medicine_name:
                continue
            
            # Extract dosage
            dosage = self._extract_dosage(segment)
            
            # Extract quantity
            quantity = self._extract_quantity(segment)
            
            # Extract form
            form = self._extract_form(segment)
            
            # Calculate confidence
            confidence = self._calculate_confidence(medicine_name, dosage, quantity)
            
            medicines.append({
                "name": medicine_name.title(),
                "dosage": dosage,
                "quantity": quantity,
                "form": form,
                "confidence": confidence
            })
        
        # Determine next action
        requires_clarification = len(medicines) == 0
        next_action = "confirm" if medicines else "ask_details"
        overall_confidence = sum(m['confidence'] for m in medicines) / len(medicines) if medicines else 0.0
        
        # Generate response
        response = self._generate_response(medicines, requires_clarification)
        
        return {
            "medicines": medicines,
            "requires_clarification": requires_clarification,
            "next_action": next_action,
            "confidence": overall_confidence,
            "response": response
        }
    
    def _extract_medicine_name(self, text: str) -> Optional[str]:
        """Extract medicine name from text"""
        text_lower = text.lower()
        
        # Check against known medicines
        for standard_name, variants in COMMON_MEDICINES.items():
            for variant in variants:
                if variant in text_lower:
                    return standard_name
        
        # Try to extract unknown medicine names (capitalized words near dosage)
        words = text.split()
        for i, word in enumerate(words):
            # Look for capitalized words or words before dosage
            if word[0].isupper() or (i < len(words) - 1 and any(unit in words[i+1].lower() for unit in ['mg', 'g', 'ml'])):
                # Clean the word
                clean_word = re.sub(r'[^\w\s]', '', word)
                if len(clean_word) > 2:
                    return clean_word.lower()
        
        return None
    
    def _extract_dosage(self, text: str) -> Optional[str]:
        """Extract dosage from text"""
        match = self.dosage_pattern.search(text)
        if match:
            amount, unit = match.groups()
            return f"{amount}{unit.lower()}"
        return None
    
    def _extract_quantity(self, text: str) -> int:
        """Extract quantity from text"""
        # Try specific quantity pattern first
        match = self.quantity_pattern.search(text)
        if match:
            return int(match.group(1))
        
        # Try simple number pattern
        match = self.simple_quantity.search(text)
        if match:
            return int(match.group(1))
        
        # Look for standalone numbers (be conservative)
        numbers = re.findall(r'\b(\d+)\b', text)
        if numbers:
            # Take the largest reasonable number (between 1-1000)
            for num_str in sorted(numbers, key=lambda x: int(x), reverse=True):
                num = int(num_str)
                if 1 <= num <= 1000:
                    return num
        
        # Default to common pack size
        return 30
    
    def _extract_form(self, text: str) -> str:
        """Extract medicine form (tablet, capsule, etc.)"""
        text_lower = text.lower()
        
        forms = {
            'tablet': ['tablet', 'tab', 'pill'],
            'capsule': ['capsule', 'cap'],
            'syrup': ['syrup', 'liquid', 'solution'],
            'injection': ['injection', 'inject', 'vial'],
            'cream': ['cream', 'ointment', 'gel'],
            'drops': ['drops', 'eye drops', 'ear drops'],
            'inhaler': ['inhaler', 'puff'],
            'patch': ['patch', 'transdermal']
        }
        
        for form_name, keywords in forms.items():
            if any(keyword in text_lower for keyword in keywords):
                return form_name
        
        return 'tablet'  # Default
    
    def _calculate_confidence(self, medicine_name: Optional[str], dosage: Optional[str], quantity: int) -> float:
        """Calculate confidence score"""
        score = 0.0
        
        # Medicine name found
        if medicine_name:
            score += 0.4
            # Known medicine gets bonus
            if medicine_name in COMMON_MEDICINES:
                score += 0.2
        
        # Dosage specified
        if dosage:
            score += 0.2
        
        # Quantity specified (not default)
        if quantity and quantity != 30:
            score += 0.2
        
        return min(score, 1.0)
    
    def _generate_response(self, medicines: List[Dict], requires_clarification: bool) -> str:
        """Generate conversational response"""
        if requires_clarification:
            return "I'd be happy to help you order medicines. Could you please tell me which medicine you need? For example, 'I need Paracetamol 500mg, 30 tablets'."
        
        if len(medicines) == 1:
            med = medicines[0]
            parts = [f"I'll add {med['name']}"]
            if med['dosage']:
                parts.append(f"{med['dosage']}")
            parts.append(f"{med['quantity']} {med['form']}s")
            
            response = ' '.join(parts) + " to your cart. "
            
            # Ask for confirmation if low confidence
            if med['confidence'] < 0.7:
                response += "Is this correct, or would you like to modify it?"
            else:
                response += "Would you like to add anything else or proceed to checkout?"
            
            return response
        
        # Multiple medicines
        response = "I'll add these medicines to your cart:\n"
        for i, med in enumerate(medicines, 1):
            parts = [f"{i}. {med['name']}"]
            if med['dosage']:
                parts.append(f"{med['dosage']}")
            parts.append(f"- {med['quantity']} {med['form']}s")
            response += ' '.join(parts) + "\n"
        
        response += "\nWould you like to add anything else or proceed to checkout?"
        return response
