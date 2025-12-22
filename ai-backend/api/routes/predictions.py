from fastapi import APIRouter, Depends
from core.database import get_database
from agents.forecast_agent import ForecastAgent

router = APIRouter()
forecast_agent = ForecastAgent()

@router.get("/user/{user_id}")
async def get_user_predictions(user_id: str, db=Depends(get_database)):
    """Get all predictions for a user"""
    predictions = await db.predictions.find({"user_id": user_id, "status": "active"}).to_list(length=100)
    return {"predictions": predictions}

@router.post("/generate/{user_id}")
async def generate_predictions(user_id: str, db=Depends(get_database)):
    """Generate new predictions for user based on order history"""
    # Get user's order history grouped by medicine
    orders = await db.orders.find({"user_id": user_id, "status": "delivered"}).sort("created_at", 1).to_list(length=1000)
    
    # Group by medicine
    from collections import defaultdict
    medicine_orders = defaultdict(list)
    
    for order in orders:
        for item in order.get('items', []):
            medicine_orders[item['medicine_id']].append({
                "medicine_name": item['medicine_name'],
                "quantity": item['quantity'],
                "order_date": order['created_at']
            })
    
    # Generate predictions
    predictions = await forecast_agent.generate_predictions_for_user(user_id, medicine_orders)
    
    # Save predictions to database
    for pred in predictions:
        await db.predictions.update_one(
            {"user_id": user_id, "medicine_id": pred['medicine_id']},
            {"$set": pred},
            upsert=True
        )
    
    return {"message": f"Generated {len(predictions)} predictions", "predictions": predictions}
