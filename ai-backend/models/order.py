from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from bson import ObjectId
from enum import Enum

from models.user import PyObjectId


class OrderStatus(str, Enum):
    """Order status enum"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderSource(str, Enum):
    """Order source enum"""
    VOICE = "voice"
    TEXT = "text"
    WEB = "web"
    MOBILE = "mobile"
    PREDICTION = "prediction"  # Auto-generated from prediction


class OrderItemBase(BaseModel):
    """Base order item model"""
    medicine_id: str
    medicine_name: str
    quantity: int
    unit_price: float
    total_price: float
    dosage: Optional[str] = None
    prescription_uploaded: bool = False
    prescription_url: Optional[str] = None


class OrderBase(BaseModel):
    """Base order model"""
    user_id: str
    items: List[OrderItemBase]
    subtotal: float
    tax: float = 0.0
    delivery_fee: float = 0.0
    total: float
    status: OrderStatus = OrderStatus.PENDING
    source: OrderSource
    notes: Optional[str] = None
    delivery_address: Optional[Dict[str, str]] = None
    conversation_id: Optional[str] = None  # Link to agent conversation


class OrderCreate(OrderBase):
    """Order creation model"""
    pass


class OrderUpdate(BaseModel):
    """Order update model"""
    status: Optional[OrderStatus] = None
    notes: Optional[str] = None


class OrderInDB(OrderBase):
    """Order in database model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    order_number: str  # Unique order number
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    agent_processed: bool = False  # Processed by AI agent
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class Order(OrderBase):
    """Order response model"""
    id: str
    order_number: str
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class VoiceOrderRequest(BaseModel):
    """Voice order request"""
    audio_base64: str  # Base64 encoded audio
    user_id: str
    language: str = "en"


class TextOrderRequest(BaseModel):
    """Text order request"""
    message: str
    user_id: str
    conversation_id: Optional[str] = None
    language: str = "en"


class AgentResponse(BaseModel):
    """AI agent response"""
    message: str
    parsed_medicines: List[dict] = []
    suggested_alternatives: List[dict] = []
    requires_prescription: bool = False
    confidence: float = 0.0
    conversation_id: str
    next_action: Optional[str] = None  # "confirm", "ask_details", "complete"


class CartItem(BaseModel):
    """Shopping cart item"""
    medicine_id: str
    medicine_name: str
    quantity: int
    unit_price: float
    total_price: float


class Cart(BaseModel):
    """Shopping cart"""
    user_id: str
    items: List[CartItem]
    subtotal: float
    total: float
    updated_at: datetime
