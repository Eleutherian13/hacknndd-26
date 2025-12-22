"""
Test script for Phase 1 - AI Backend Test Endpoints
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """Test health check"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/ai/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_create_order():
    """Test creating a test order"""
    print("\n=== Testing Create Test Order ===")
    order_data = {
        "user_id": "test_user_123",
        "medicine_name": "Paracetamol 500mg",
        "quantity": 30,
        "notes": f"Phase 1 test order - {datetime.now().isoformat()}"
    }
    
    print(f"Sending: {json.dumps(order_data, indent=2)}")
    response = requests.post(f"{BASE_URL}/ai/test", json=order_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        return response.json().get("order_id")
    return None

def test_get_orders(user_id):
    """Test retrieving user orders"""
    print(f"\n=== Testing Get Orders for User: {user_id} ===")
    response = requests.get(f"{BASE_URL}/ai/orders/{user_id}")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total orders: {data.get('total_count', 0)}")
    print(f"Test orders: {len(data.get('test_orders', []))}")
    print(f"Actual orders: {len(data.get('actual_orders', []))}")
    
    if data.get('test_orders'):
        print("\nRecent test orders:")
        for order in data['test_orders'][:3]:
            print(f"  - {order.get('medicine_name')} x{order.get('quantity')} ({order.get('status')})")
    
    return response.status_code == 200

def test_multiple_orders():
    """Test creating multiple orders"""
    print("\n=== Testing Multiple Orders ===")
    medicines = [
        {"name": "Aspirin 100mg", "qty": 50},
        {"name": "Amoxicillin 500mg", "qty": 20},
        {"name": "Metformin 850mg", "qty": 60},
        {"name": "Omeprazole 20mg", "qty": 30},
    ]
    
    created = 0
    for med in medicines:
        order_data = {
            "user_id": "test_user_123",
            "medicine_name": med["name"],
            "quantity": med["qty"],
            "notes": "Bulk test order"
        }
        response = requests.post(f"{BASE_URL}/ai/test", json=order_data)
        if response.status_code == 200:
            created += 1
            print(f"✓ Created: {med['name']}")
        else:
            print(f"✗ Failed: {med['name']}")
    
    print(f"\nCreated {created}/{len(medicines)} orders")
    return created == len(medicines)

if __name__ == "__main__":
    print("="*60)
    print("PHASE 1: AI Backend Test Suite")
    print("="*60)
    
    results = {}
    
    # Test 1: Health check
    results['health'] = test_health()
    
    # Test 2: Create single order
    order_id = test_create_order()
    results['create_order'] = order_id is not None
    
    # Test 3: Get orders
    results['get_orders'] = test_get_orders("test_user_123")
    
    # Test 4: Create multiple orders
    results['bulk_orders'] = test_multiple_orders()
    
    # Test 5: Verify all orders retrieved
    results['verify_orders'] = test_get_orders("test_user_123")
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name.ljust(20)}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nOverall: {passed}/{total} tests passed")
    print("="*60)
