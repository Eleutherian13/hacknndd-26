from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import logging

from models.order import (
    TextOrderRequest,
    VoiceOrderRequest,
    AgentResponse,
    Order,
    OrderCreate
)
from models.user import User
from agents.ordering_agent import OrderingAgent
from agents.safety_agent import SafetyAgent
from core.database import get_database
from core.websocket_manager import manager
import base64
import io

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize agents
ordering_agent = OrderingAgent()
safety_agent = SafetyAgent()


@router.post("/text", response_model=AgentResponse)
async def process_text_order(
    request: TextOrderRequest,
    db=Depends(get_database)
):
    """
    Process text-based order request
    
    Customer types their medicine request and the AI agent responds
    """
    try:
        # Get conversation history from database
        conversation_history = await db.conversations.find_one({
            "user_id": request.user_id,
            "conversation_id": request.conversation_id
        }) or {"messages": []}
        
        # Get user context with fallback
        user = await db.users.find_one({"_id": request.user_id})
        if not user:
            # Create minimal user context if user not found
            user_context = {
                "name": "User",
                "language": request.language,
                "current_medications": []
            }
            logger.warning(f"User {request.user_id} not found in database, using minimal context")
        else:
            user_context = {
                "name": user.get('full_name') or user.get('name', 'User'),
                "language": user.get('language', request.language),
                "current_medications": user.get('onboarding_data', {}).get('current_medications', [])
            }
        
        # Process message with ordering agent
        try:
            agent_response = await ordering_agent.process_message(
                message=request.message,
                conversation_history=conversation_history.get("messages", []),
                user_context=user_context,
                language=request.language
            )
        except Exception as agent_error:
            logger.error(f"Error in ordering agent: {str(agent_error)}")
            # Fallback response if agent fails
            agent_response = {
                "message": f"I received your message: '{request.message}'. I'm here to help you order medicines. Could you please tell me which specific medicines you need?",
                "parsed_medicines": [],
                "confidence": 0.5,
                "next_action": "clarify_order"
            }
        
        # Save conversation
        conversation_id = request.conversation_id or f"conv_{request.user_id}_{int(datetime.now().timestamp())}"
        
        await db.conversations.update_one(
            {"conversation_id": conversation_id},
            {
                "$push": {
                    "messages": {
                        "$each": [
                            {"role": "user", "content": request.message, "timestamp": datetime.now()},
                            {"role": "assistant", "content": agent_response["message"], "timestamp": datetime.now()}
                        ]
                    }
                },
                "$set": {
                    "user_id": request.user_id,
                    "updated_at": datetime.now()
                }
            },
            upsert=True
        )
        
        # Send real-time update to user
        await manager.notify_agent_message(
            user_id=request.user_id,
            agent_type="ordering",
            message_text=agent_response["message"]
        )
        
        logger.info(f"Processed text order for user {request.user_id}")
        
        return AgentResponse(
            response=agent_response["message"],
            message=agent_response["message"],
            parsed_medicines=agent_response.get("parsed_medicines", []),
            requires_prescription=any(m.get('prescription_required') for m in agent_response.get("parsed_medicines", [])),
            confidence=agent_response.get("confidence", 0.0),
            conversation_id=conversation_id,
            next_action=agent_response.get("next_action")
        )
        
    except Exception as e:
        logger.error(f"Error processing text order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing order: {str(e)}"
        )


@router.post("/voice", response_model=AgentResponse)
async def process_voice_order(
    request: VoiceOrderRequest,
    db=Depends(get_database)
):
    """
    Process voice-based order request
    
    Customer speaks their medicine request, it's transcribed, and AI responds
    """
    try:
        # Decode base64 audio
        audio_bytes = base64.b64decode(request.audio_base64)
        
        # Transcribe audio using OpenAI Whisper
        from openai import OpenAI
        from core.config import settings
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Save audio temporarily
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav"
        
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=request.language
        )
        
        transcribed_text = transcription.text
        logger.info(f"Transcribed: {transcribed_text}")
        
        # Process as text order
        text_request = TextOrderRequest(
            message=transcribed_text,
            user_id=request.user_id,
            language=request.language
        )
        
        return await process_text_order(text_request, db)
        
    except Exception as e:
        logger.error(f"Error processing voice order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing voice order: {str(e)}"
        )


@router.post("/confirm", response_model=Order)
async def confirm_order(
    order_data: OrderCreate,
    db=Depends(get_database)
):
    """
    Confirm and create order after user approves
    """
    try:
        # Get user profile for safety check
        user = await db.users.find_one({"_id": order_data.user_id})
        user_profile = {
            "current_medications": user.get('onboarding_data', {}).get('current_medications', []),
            "allergies": user.get('onboarding_data', {}).get('allergies', [])
        }
        
        # Perform safety check
        safety_check = await safety_agent.comprehensive_safety_check(
            order_items=order_data.items,
            user_profile=user_profile
        )
        
        if not safety_check.get('overall_safe'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Order requires pharmacist review due to safety concerns",
                    "safety_check": safety_check
                }
            )
        
        # Generate order number
        order_count = await db.orders.count_documents({})
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{order_count + 1:04d}"
        
        # Create order
        order_dict = order_data.dict()
        order_dict["order_number"] = order_number
        order_dict["created_at"] = datetime.now()
        order_dict["updated_at"] = datetime.now()
        order_dict["agent_processed"] = True
        
        result = await db.orders.insert_one(order_dict)
        
        # Update inventory (decrement stock)
        for item in order_data.items:
            await db.inventory.update_one(
                {"medicine_id": item.medicine_id},
                {"$inc": {"quantity": -item.quantity}}
            )
        
        # Notify user
        await manager.notify_order_update(
            user_id=order_data.user_id,
            order_data={
                "order_id": str(result.inserted_id),
                "order_number": order_number,
                "status": "confirmed",
                "message": "Your order has been confirmed!"
            }
        )
        
        logger.info(f"Order confirmed: {order_number}")
        
        # Return created order
        created_order = await db.orders.find_one({"_id": result.inserted_id})
        created_order["id"] = str(created_order.pop("_id"))
        
        return Order(**created_order)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error confirming order: {str(e)}"
        )


@router.get("/{order_id}", response_model=Order)
async def get_order(
    order_id: str,
    db=Depends(get_database)
):
    """Get order details"""
    try:
        order = await db.orders.find_one({"_id": order_id})
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        order["id"] = str(order.pop("_id"))
        return Order(**order)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/user/{user_id}", response_model=List[Order])
async def get_user_orders(
    user_id: str,
    limit: int = 20,
    skip: int = 0,
    db=Depends(get_database)
):
    """Get all orders for a user"""
    try:
        cursor = db.orders.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit)
        orders = await cursor.to_list(length=limit)
        
        for order in orders:
            order["id"] = str(order.pop("_id"))
        
        return [Order(**order) for order in orders]
        
    except Exception as e:
        logger.error(f"Error getting user orders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


from datetime import datetime
