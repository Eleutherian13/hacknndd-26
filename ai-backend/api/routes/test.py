from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

from core.database import get_database

router = APIRouter()
logger = logging.getLogger(__name__)


class TestOrder(BaseModel):
    user_id: str
    medicine_name: str
    quantity: int
    notes: Optional[str] = None


class TestOrderResponse(BaseModel):
    success: bool
    message: str
    order_id: str


@router.post("/test", response_model=TestOrderResponse)
async def create_test_order(
    order: TestOrder,
    db=Depends(get_database)
):
    """
    Phase 1: Test endpoint to save a sample order to MongoDB
    
    Example:
    POST /ai/test
    {
        "user_id": "123",
        "medicine_name": "Paracetamol",
        "quantity": 20,
        "notes": "Test order"
    }
    """
    try:
        # Create order document
        order_doc = {
            "user_id": order.user_id,
            "medicine_name": order.medicine_name,
            "quantity": order.quantity,
            "notes": order.notes,
            "status": "test",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert into MongoDB
        result = await db.test_orders.insert_one(order_doc)
        
        logger.info(f"Test order created: {result.inserted_id}")
        
        return TestOrderResponse(
            success=True,
            message="Test order saved successfully",
            order_id=str(result.inserted_id)
        )
        
    except Exception as e:
        logger.error(f"Error creating test order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating test order: {str(e)}"
        )


@router.get("/orders/{user_id}")
async def get_user_orders(
    user_id: str,
    db=Depends(get_database)
):
    """
    Phase 1: Retrieve user orders from MongoDB
    
    Example:
    GET /ai/orders/123
    """
    try:
        # Query test orders
        test_orders = []
        async for order in db.test_orders.find({"user_id": user_id}):
            order["_id"] = str(order["_id"])
            test_orders.append(order)
        
        # Query actual orders
        actual_orders = []
        async for order in db.orders.find({"user_id": user_id}):
            order["_id"] = str(order["_id"])
            actual_orders.append(order)
        
        logger.info(f"Retrieved orders for user {user_id}: {len(test_orders)} test, {len(actual_orders)} actual")
        
        return {
            "success": True,
            "user_id": user_id,
            "test_orders": test_orders,
            "actual_orders": actual_orders,
            "total_count": len(test_orders) + len(actual_orders)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving orders: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving orders: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-backend",
        "timestamp": datetime.utcnow().isoformat()
    }
