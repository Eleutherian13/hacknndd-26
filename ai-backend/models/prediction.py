from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, date
from bson import ObjectId
from enum import Enum

from models.user import PyObjectId


class PredictionStatus(str, Enum):
    """Prediction status"""
    ACTIVE = "active"
    NOTIFIED = "notified"
    ORDERED = "ordered"
    EXPIRED = "expired"


class PredictionConfidence(str, Enum):
    """Prediction confidence levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PredictionBase(BaseModel):
    """Base prediction model"""
    user_id: str
    medicine_id: str
    medicine_name: str
    average_consumption_rate: float  # pills/day or ml/day
    last_order_date: date
    last_order_quantity: int
    predicted_depletion_date: date
    suggested_reorder_date: date
    suggested_quantity: int
    confidence: PredictionConfidence
    confidence_score: float  # 0.0 to 1.0
    status: PredictionStatus = PredictionStatus.ACTIVE


class PredictionCreate(PredictionBase):
    """Prediction creation model"""
    pass


class PredictionUpdate(BaseModel):
    """Prediction update model"""
    status: Optional[PredictionStatus] = None
    predicted_depletion_date: Optional[date] = None
    suggested_reorder_date: Optional[date] = None


class PredictionInDB(PredictionBase):
    """Prediction in database model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    notified_at: Optional[datetime] = None
    ordered_at: Optional[datetime] = None
    historical_data: List[Dict] = []  # Historical order data used for prediction
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class Prediction(PredictionBase):
    """Prediction response model"""
    id: str
    created_at: datetime
    notified_at: Optional[datetime] = None
    days_until_depletion: int
    
    class Config:
        from_attributes = True


class PredictionTimeline(BaseModel):
    """Prediction timeline for visualization"""
    medicine_name: str
    last_order_date: date
    predicted_depletion_date: date
    suggested_reorder_date: date
    current_date: date
    days_remaining: int
    consumption_history: List[Dict]  # Historical consumption data


class UserPredictions(BaseModel):
    """All predictions for a user"""
    user_id: str
    total_predictions: int
    active_predictions: int
    upcoming_depletions: List[Prediction]
    timelines: List[PredictionTimeline]


class PredictionAnalytics(BaseModel):
    """Prediction analytics"""
    total_predictions: int
    accuracy_rate: float  # Percentage of accurate predictions
    average_confidence: float
    predictions_by_status: Dict[str, int]
    top_predicted_medicines: List[Dict]
