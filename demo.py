#!/usr/bin/env python3
"""
Mediloon AI Pharmacy - Quick Demo Script
Demonstrates the multi-agent system in action
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from agents.ordering_agent import OrderingAgent
from agents.forecast_agent import ForecastAgent
from agents.safety_agent import SafetyAgent
from agents.procurement_agent import ProcurementAgent
from datetime import datetime, timedelta


async def demo_ordering_agent():
    """Demo: Customer orders medicine via text"""
    print("\n" + "="*70)
    print("DEMO 1: Text-Based Medicine Ordering")
    print("="*70)
    
    agent = OrderingAgent()
    
    # Simulate customer conversation
    messages = [
        "Hi, I need medicine for headache",
        "I'll take Aspirin 100mg, 30 tablets please",
        "Yes, please add it to my cart"
    ]
    
    conversation_history = []
    user_context = {"name": "John Doe", "language": "en"}
    
    for i, message in enumerate(messages, 1):
        print(f"\n👤 Customer: {message}")
        
        response = await agent.process_message(
            message=message,
            conversation_history=conversation_history,
            user_context=user_context,
            language="en"
        )
        
        print(f"🤖 AI Agent: {response['message']}")
        
        if response['parsed_medicines']:
            print(f"\n📦 Parsed Items:")
            for med in response['parsed_medicines']:
                print(f"   - {med['name']} {med.get('dosage', '')} x{med.get('quantity', 1)}")
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": response['message']})
        
        await asyncio.sleep(1)


async def demo_forecast_agent():
    """Demo: Predict medicine depletion"""
    print("\n" + "="*70)
    print("DEMO 2: Predictive Medicine Depletion Forecast")
    print("="*70)
    
    agent = ForecastAgent()
    
    # Simulate order history for a chronic medication (Metformin for diabetes)
    order_history = [
        {"order_date": datetime.now() - timedelta(days=90), "quantity": 60, "medicine_name": "Metformin 500mg"},
        {"order_date": datetime.now() - timedelta(days=60), "quantity": 60, "medicine_name": "Metformin 500mg"},
        {"order_date": datetime.now() - timedelta(days=30), "quantity": 60, "medicine_name": "Metformin 500mg"},
        {"order_date": datetime.now(), "quantity": 60, "medicine_name": "Metformin 500mg"},
    ]
    
    print(f"\n📊 Order History:")
    for i, order in enumerate(order_history, 1):
        print(f"   {i}. {order['order_date'].strftime('%Y-%m-%d')} - {order['quantity']} tablets")
    
    print(f"\n🔮 Analyzing consumption pattern...")
    await asyncio.sleep(1)
    
    prediction = await agent.predict_depletion(
        user_id="demo_user",
        medicine_id="metformin_500",
        order_history=order_history
    )
    
    if prediction:
        print(f"\n✅ Prediction Generated:")
        print(f"   📈 Consumption Rate: {prediction['average_consumption_rate']:.2f} tablets/day")
        print(f"   📅 Last Order: {prediction['last_order_date']}")
        print(f"   ⚠️  Predicted Depletion: {prediction['predicted_depletion_date']}")
        print(f"   🔔 Suggested Reorder: {prediction['suggested_reorder_date']}")
        print(f"   📦 Suggested Quantity: {prediction['suggested_quantity']} tablets")
        print(f"   🎯 Confidence: {prediction['confidence'].value.upper()} ({prediction['confidence_score']:.0%})")
        
        days_remaining = (prediction['predicted_depletion_date'] - datetime.now().date()).days
        print(f"\n💡 You have approximately {days_remaining} days of supply remaining")
    else:
        print("❌ Insufficient data for prediction")


async def demo_safety_agent():
    """Demo: Drug interaction checking"""
    print("\n" + "="*70)
    print("DEMO 3: Drug Interaction & Safety Check")
    print("="*70)
    
    agent = SafetyAgent()
    
    # Simulate a patient ordering new medicine who already takes other medications
    new_medicines = [
        {"name": "Warfarin", "medicine_name": "Warfarin", "dosage": "5mg"}
    ]
    
    existing_medications = [
        {"name": "Aspirin", "medicine_name": "Aspirin 100mg"},
        {"name": "Vitamin K", "medicine_name": "Vitamin K supplement"}
    ]
    
    print(f"\n🆕 New Medicine Being Ordered:")
    for med in new_medicines:
        print(f"   - {med['name']} {med.get('dosage', '')}")
    
    print(f"\n💊 Current Medications:")
    for med in existing_medications:
        print(f"   - {med['name']}")
    
    print(f"\n🔍 Checking for drug interactions...")
    await asyncio.sleep(2)
    
    interaction_check = await agent.check_drug_interactions(
        new_medicines=new_medicines,
        existing_medications=existing_medications
    )
    
    if interaction_check['has_interactions']:
        print(f"\n⚠️  INTERACTION WARNINGS FOUND:")
        for warning in interaction_check['warnings']:
            severity_emoji = "🔴" if warning['severity'] == 'critical' else "🟡"
            print(f"   {severity_emoji} {warning['severity'].upper()}: {warning['message']}")
            print(f"      Action: {warning['action']}")
    else:
        print(f"\n✅ No significant drug interactions detected")
    
    print(f"\n📋 Recommendation: {interaction_check.get('recommendation', 'Consult pharmacist')}")
    print(f"🛡️  Safe to Proceed: {'YES' if interaction_check['safe_to_proceed'] else 'NO - REQUIRES REVIEW'}")


async def demo_procurement_agent():
    """Demo: Automated procurement"""
    print("\n" + "="*70)
    print("DEMO 4: Automated Procurement System")
    print("="*70)
    
    agent = ProcurementAgent()
    
    # Simulate low inventory scenario
    print(f"\n📊 Current Inventory Status:")
    inventory_items = [
        {"medicine_id": "asp100", "medicine_name": "Aspirin 100mg", "sku": "ASP100", "current_stock": 50, "reorder_threshold": 100, "pending_orders": 30},
        {"medicine_id": "ibu200", "medicine_name": "Ibuprofen 200mg", "sku": "IBU200", "current_stock": 20, "reorder_threshold": 80, "pending_orders": 10},
        {"medicine_id": "par500", "medicine_name": "Paracetamol 500mg", "sku": "PAR500", "current_stock": 200, "reorder_threshold": 100, "pending_orders": 50},
    ]
    
    procurement_needed = []
    
    for item in inventory_items:
        effective_stock = item['current_stock'] - item['pending_orders']
        status = "🔴 LOW" if effective_stock < item['reorder_threshold'] else "🟢 OK"
        print(f"   {status} {item['medicine_name']}: {item['current_stock']} units (Pending: {item['pending_orders']}, Threshold: {item['reorder_threshold']})")
        
        # Check if procurement needed
        check = await agent.check_inventory_need(
            medicine_id=item['medicine_id'],
            current_stock=item['current_stock'],
            reorder_threshold=item['reorder_threshold'],
            pending_orders=item['pending_orders']
        )
        
        if check['needs_procurement']:
            procurement_needed.append({
                **item,
                'quantity': check['suggested_quantity'],
                'urgency': check['urgency']
            })
    
    if procurement_needed:
        print(f"\n⚠️  {len(procurement_needed)} items need procurement")
        
        print(f"\n📝 Generating Purchase Order...")
        await asyncio.sleep(1)
        
        supplier_info = {
            "name": "MediSupply Corp",
            "email": "orders@medisupply.com",
            "phone": "+1-555-0123"
        }
        
        po = await agent.generate_purchase_order(
            procurement_items=procurement_needed,
            supplier_info=supplier_info
        )
        
        if po and not po.get('error'):
            print(f"\n✅ Purchase Order Generated:")
            print(f"   PO Number: {po['po_number']}")
            print(f"   Supplier: {supplier_info['name']}")
            print(f"   Total Items: {po['total_items']}")
            print(f"   Total Quantity: {po['total_quantity']} units")
            
            print(f"\n📧 Generated Email:")
            print("   " + "-"*60)
            for line in po['generated_email'].split('\n')[:10]:  # Show first 10 lines
                print(f"   {line}")
            print("   " + "-"*60)
            
            print(f"\n📤 Ready to send to supplier via n8n/Zapier integration")
    else:
        print(f"\n✅ All inventory levels are sufficient")


async def main():
    """Run all demos"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  🏥 MEDILOON AI PHARMACY - MULTI-AGENT SYSTEM DEMO  🤖".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    try:
        await demo_ordering_agent()
        await asyncio.sleep(2)
        
        await demo_forecast_agent()
        await asyncio.sleep(2)
        
        await demo_safety_agent()
        await asyncio.sleep(2)
        
        await demo_procurement_agent()
        
        print("\n" + "="*70)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*70)
        print("\n💡 These demos show the power of AI agents working together to:")
        print("   1. Understand natural language orders")
        print("   2. Predict medicine needs proactively")
        print("   3. Ensure patient safety")
        print("   4. Automate procurement workflows")
        print("\n🚀 Ready for production deployment!\n")
        
    except Exception as e:
        print(f"\n❌ Error running demo: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check if OpenAI API key is set
    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  WARNING: OPENAI_API_KEY not set in environment")
        print("   The demos will simulate responses without actual API calls")
        print("   To enable full functionality, set your API key:\n")
        print("   export OPENAI_API_KEY='your-api-key-here'  # Mac/Linux")
        print("   $env:OPENAI_API_KEY='your-api-key-here'   # Windows PowerShell\n")
    
    asyncio.run(main())
