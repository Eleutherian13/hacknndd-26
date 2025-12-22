from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
import logging
import uuid

from core.database import get_database
from agents.ordering_agent import OrderingAgent

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize agent
ordering_agent = OrderingAgent()


class OrderMessage(BaseModel):
    """Message for ordering conversation"""
    message: str = Field(..., min_length=1, description="User message (voice or text)")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    user_id: Optional[str] = Field(None, description="User ID")
    language: str = Field("en", description="Language code (en, de, ar)")


class OrderResponse(BaseModel):
    """Response from ordering agent"""
    message: str
    response: str  # For backward compatibility
    conversation_id: str
    parsed_medicines: List[Dict]
    requires_clarification: bool
    next_action: str
    confidence: float
    timestamp: datetime


class CartItem(BaseModel):
    """Cart item structure"""
    medicine_name: str
    dosage: Optional[str] = None
    quantity: int
    form: Optional[str] = "tablet"
    unit_price: Optional[float] = None


class CartSummary(BaseModel):
    """Cart summary response"""
    user_id: str
    items: List[CartItem]
    total_items: int
    estimated_total: float
    requires_prescription: bool


@router.post("/chat", response_model=OrderResponse)
async def order_chat(
    order_msg: OrderMessage,
    db=Depends(get_database)
):
    """
    Phase 2: Enhanced ordering endpoint with LangChain agent
    
    Handles natural language medicine ordering with:
    - Medicine name/dosage/quantity parsing
    - Multi-turn conversations
    - Clarification questions
    - Context awareness
    
    Example:
    POST /orders/chat
    {
        "message": "I need 20 tablets of Paracetamol 500mg",
        "user_id": "123",
        "language": "en"
    }
    """
    try:
        # Generate conversation ID if not provided
        conversation_id = order_msg.conversation_id or str(uuid.uuid4())
        
        # Get conversation history from database
        conversation_history = []
        if order_msg.conversation_id:
            history_docs = await db.conversations.find(
                {"conversation_id": conversation_id}
            ).sort("timestamp", 1).to_list(length=50)
            
            conversation_history = [
                {
                    "role": doc.get("role"),
                    "content": doc.get("content"),
                    "timestamp": doc.get("timestamp")
                }
                for doc in history_docs
            ]
        
        # Get user context
        user_context = {"name": "Customer"}
        if order_msg.user_id:
            user_doc = await db.users.find_one({"_id": order_msg.user_id})
            if user_doc:
                user_context = {
                    "name": user_doc.get("name", "Customer"),
                    "email": user_doc.get("email"),
                    "phone": user_doc.get("phone"),
                    "address": user_doc.get("address"),
                    "preferences": user_doc.get("preferences", {})
                }
        
        # Process message with ordering agent
        result = await ordering_agent.process_message(
            message=order_msg.message,
            conversation_history=conversation_history,
            user_context=user_context,
            language=order_msg.language
        )
        
        # Save conversation to database
        await db.conversations.insert_one({
            "conversation_id": conversation_id,
            "user_id": order_msg.user_id,
            "role": "user",
            "content": order_msg.message,
            "timestamp": datetime.utcnow()
        })
        
        await db.conversations.insert_one({
            "conversation_id": conversation_id,
            "user_id": order_msg.user_id,
            "role": "assistant",
            "content": result["message"],
            "parsed_data": result.get("parsed_medicines", []),
            "timestamp": datetime.utcnow()
        })
        
        # If medicines were parsed, add them to temporary cart
        if result.get("parsed_medicines"):
            for medicine in result["parsed_medicines"]:
                await db.cart_items.update_one(
                    {
                        "user_id": order_msg.user_id,
                        "conversation_id": conversation_id,
                        "medicine_name": medicine.get("name")
                    },
                    {
                        "$set": {
                            "dosage": medicine.get("dosage"),
                            "quantity": medicine.get("quantity", 1),
                            "form": medicine.get("form", "tablet"),
                            "confidence": medicine.get("confidence", 0.7),
                            "updated_at": datetime.utcnow()
                        },
                        "$setOnInsert": {
                            "created_at": datetime.utcnow()
                        }
                    },
                    upsert=True
                )
        
        logger.info(f"Chat processed for conversation {conversation_id}")
        
        return OrderResponse(
            message=result["message"],
            response=result["message"],  # For backward compatibility
            conversation_id=conversation_id,
            parsed_medicines=result.get("parsed_medicines", []),
            requires_clarification=result.get("requires_clarification", False),
            next_action=result.get("next_action", "continue"),
            confidence=result.get("confidence", 0.7),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in order chat: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing order chat: {str(e)}"
        )


@router.get("/cart/{user_id}", response_model=CartSummary)
async def get_cart(
    user_id: str,
    conversation_id: Optional[str] = None,
    db=Depends(get_database)
):
    """
    Get current cart contents for a user
    
    Example:
    GET /orders/cart/123?conversation_id=abc-def-123
    """
    try:
        # Build query
        query = {"user_id": user_id}
        if conversation_id:
            query["conversation_id"] = conversation_id
        
        # Get cart items
        cart_docs = await db.cart_items.find(query).to_list(length=100)
        
        items = []
        total_estimate = 0.0
        requires_prescription = False
        
        for doc in cart_docs:
            # Estimate price (would normally look up from database)
            unit_price = 10.0  # Default estimate
            item_total = doc.get("quantity", 1) * unit_price
            total_estimate += item_total
            
            items.append(CartItem(
                medicine_name=doc.get("medicine_name"),
                dosage=doc.get("dosage"),
                quantity=doc.get("quantity", 1),
                form=doc.get("form", "tablet"),
                unit_price=unit_price
            ))
        
        logger.info(f"Cart retrieved for user {user_id}: {len(items)} items")
        
        return CartSummary(
            user_id=user_id,
            items=items,
            total_items=len(items),
            estimated_total=total_estimate,
            requires_prescription=requires_prescription
        )
        
    except Exception as e:
        logger.error(f"Error getting cart: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving cart: {str(e)}"
        )


@router.post("/cart/{user_id}/confirm")
async def confirm_cart(
    user_id: str,
    conversation_id: Optional[str] = None,
    db=Depends(get_database)
):
    """
    Confirm cart and create order
    
    Example:
    POST /orders/cart/123/confirm?conversation_id=abc-def-123
    """
    try:
        # Get cart items
        query = {"user_id": user_id}
        if conversation_id:
            query["conversation_id"] = conversation_id
        
        cart_docs = await db.cart_items.find(query).to_list(length=100)
        
        if not cart_docs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty"
            )
        
        # Create order
        order_items = []
        total_amount = 0.0
        
        for doc in cart_docs:
            unit_price = 10.0  # Would look up from medicines collection
            quantity = doc.get("quantity", 1)
            item_total = quantity * unit_price
            total_amount += item_total
            
            order_items.append({
                "medicine_name": doc.get("medicine_name"),
                "dosage": doc.get("dosage"),
                "quantity": quantity,
                "form": doc.get("form"),
                "unit_price": unit_price,
                "total_price": item_total
            })
        
        # Insert order
        order_doc = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "items": order_items,
            "total_amount": total_amount,
            "status": "pending",
            "payment_status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.orders.insert_one(order_doc)
        order_id = str(result.inserted_id)
        
        # Clear cart
        await db.cart_items.delete_many(query)
        
        # Generate confirmation message
        confirmation = await ordering_agent.confirm_order(
            medicines=order_items,
            user_context={"name": "Customer"}
        )
        
        logger.info(f"Order {order_id} created for user {user_id}")
        
        return {
            "success": True,
            "order_id": order_id,
            "total_amount": total_amount,
            "items_count": len(order_items),
            "confirmation_message": confirmation,
            "status": "pending"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming cart: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error confirming order: {str(e)}"
        )


@router.delete("/cart/{user_id}/clear")
async def clear_cart(
    user_id: str,
    conversation_id: Optional[str] = None,
    db=Depends(get_database)
):
    """Clear cart for user"""
    try:
        query = {"user_id": user_id}
        if conversation_id:
            query["conversation_id"] = conversation_id
        
        result = await db.cart_items.delete_many(query)
        
        return {
            "success": True,
            "deleted_count": result.deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error clearing cart: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing cart: {str(e)}"
        )
