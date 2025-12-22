"""
Test script for Phase 2 - Enhanced Ordering Agent
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_ordering_chat(message, conversation_id=None, user_id="test_user_phase2"):
    """Test the ordering chat endpoint"""
    print(f"\n{'='*60}")
    print(f"User: {message}")
    print(f"{'='*60}")
    
    payload = {
        "message": message,
        "user_id": user_id,
        "language": "en"
    }
    
    if conversation_id:
        payload["conversation_id"] = conversation_id
    
    response = requests.post(f"{BASE_URL}/orders/chat", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nBot: {data['message']}")
        print(f"\nConversation ID: {data['conversation_id']}")
        print(f"Confidence: {data['confidence']:.2f}")
        print(f"Next Action: {data['next_action']}")
        print(f"Requires Clarification: {data['requires_clarification']}")
        
        if data['parsed_medicines']:
            print(f"\n📦 Parsed Medicines ({len(data['parsed_medicines'])}):")
            for med in data['parsed_medicines']:
                print(f"  - {med.get('name')} {med.get('dosage', '')} x{med.get('quantity', 1)} ({med.get('form', 'tablet')})")
                print(f"    Confidence: {med.get('confidence', 0):.2f}")
        
        return data['conversation_id'], data
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)
        return None, None


def test_get_cart(user_id, conversation_id=None):
    """Test cart retrieval"""
    print(f"\n{'='*60}")
    print(f"🛒 Getting Cart for User: {user_id}")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}/orders/cart/{user_id}"
    if conversation_id:
        url += f"?conversation_id={conversation_id}"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nTotal Items: {data['total_items']}")
        print(f"Estimated Total: ${data['estimated_total']:.2f}")
        print(f"Requires Prescription: {data['requires_prescription']}")
        
        if data['items']:
            print(f"\nCart Items:")
            for item in data['items']:
                print(f"  - {item['medicine_name']} {item.get('dosage', '')} x{item['quantity']}")
                print(f"    ${item.get('unit_price', 0):.2f} each")
        
        return data
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)
        return None


def test_confirm_cart(user_id, conversation_id=None):
    """Test cart confirmation"""
    print(f"\n{'='*60}")
    print(f"✅ Confirming Cart for User: {user_id}")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}/orders/cart/{user_id}/confirm"
    if conversation_id:
        url += f"?conversation_id={conversation_id}"
    
    response = requests.post(url)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ Order Created!")
        print(f"Order ID: {data['order_id']}")
        print(f"Total Amount: ${data['total_amount']:.2f}")
        print(f"Items Count: {data['items_count']}")
        print(f"\nConfirmation Message:")
        print(data['confirmation_message'])
        
        return data
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)
        return None


def run_conversation_flow():
    """Run a complete conversation flow"""
    print("\n" + "="*60)
    print("PHASE 2: Enhanced Ordering Agent Test")
    print("="*60)
    
    user_id = "test_user_phase2"
    conversation_id = None
    
    # Test 1: Initial greeting and simple order
    print("\n\n### TEST 1: Simple Medicine Order ###")
    conversation_id, _ = test_ordering_chat(
        "I need Paracetamol 500mg, 30 tablets please",
        conversation_id,
        user_id
    )
    time.sleep(1)
    
    # Test 2: Add another medicine
    print("\n\n### TEST 2: Adding Another Medicine ###")
    conversation_id, _ = test_ordering_chat(
        "Can you also add Aspirin 100mg, 50 tablets?",
        conversation_id,
        user_id
    )
    time.sleep(1)
    
    # Test 3: Complex multi-medicine order
    print("\n\n### TEST 3: Multi-Medicine Order ###")
    conversation_id, _ = test_ordering_chat(
        "I also need Amoxicillin 500mg capsules, 20 count, and Vitamin D 5000 IU",
        conversation_id,
        user_id
    )
    time.sleep(1)
    
    # Test 4: Get cart
    print("\n\n### TEST 4: View Cart ###")
    cart = test_get_cart(user_id, conversation_id)
    
    # Test 5: Confirm order
    if cart and cart['total_items'] > 0:
        print("\n\n### TEST 5: Confirm Order ###")
        confirmation = test_confirm_cart(user_id, conversation_id)
        
        if confirmation:
            print("\n\n✅ FULL FLOW COMPLETED SUCCESSFULLY!")
        else:
            print("\n\n⚠️ Order confirmation failed")
    else:
        print("\n\n⚠️ Cart is empty, skipping confirmation")
    
    # Test 6: New conversation - unclear request
    print("\n\n### TEST 6: Unclear Request (Clarification Needed) ###")
    conversation_id, _ = test_ordering_chat(
        "I need something for headache",
        None,  # New conversation
        user_id
    )
    time.sleep(1)
    
    # Test 7: Follow-up with specific medicine
    print("\n\n### TEST 7: Clarification Response ###")
    conversation_id, _ = test_ordering_chat(
        "Make it Ibuprofen 200mg, 24 tablets",
        conversation_id,
        user_id
    )


def run_edge_cases():
    """Test edge cases"""
    print("\n\n" + "="*60)
    print("EDGE CASES TEST")
    print("="*60)
    
    user_id = "test_edge_cases"
    
    # Empty message
    print("\n\n### EDGE CASE 1: No Medicine Mentioned ###")
    test_ordering_chat("Hello!", None, user_id)
    time.sleep(1)
    
    # Misspelled medicine
    print("\n\n### EDGE CASE 2: Misspelled Medicine ###")
    test_ordering_chat("I need Paracitamol and Aspirine", None, user_id)
    time.sleep(1)
    
    # No quantity specified
    print("\n\n### EDGE CASE 3: No Quantity ###")
    test_ordering_chat("I need Metformin 850mg", None, user_id)
    time.sleep(1)
    
    # Multiple languages mixed (English with German)
    print("\n\n### EDGE CASE 4: Mixed Language ###")
    test_ordering_chat("I need Paracetamol and also some Aspirin bitte", None, user_id)


if __name__ == "__main__":
    try:
        print("Waiting for server to be ready...")
        time.sleep(2)
        
        # Run main conversation flow
        run_conversation_flow()
        
        # Run edge cases
        run_edge_cases()
        
        print("\n\n" + "="*60)
        print("ALL TESTS COMPLETED")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite error: {str(e)}")
        import traceback
        traceback.print_exc()
