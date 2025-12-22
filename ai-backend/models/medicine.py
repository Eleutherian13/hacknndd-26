from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from enum import Enum

from models.user import PyObjectId


class MedicineCategory(str, Enum):
    """Medicine categories"""
    PAIN_RELIEF = "pain_relief"
    ANTIBIOTICS = "antibiotics"
    CARDIOVASCULAR = "cardiovascular"
    DIABETES = "diabetes"
    RESPIRATORY = "respiratory"
    GASTROINTESTINAL = "gastrointestinal"
    VITAMINS = "vitamins"
    OTHER = "other"


class PrescriptionRequired(str, Enum):
    """Prescription requirement levels"""
    YES = "yes"
    NO = "no"
    OPTIONAL = "optional"


class MedicineBase(BaseModel):
    """Base medicine model"""
    name: str
    generic_name: Optional[str] = None
    brand_name: Optional[str] = None
    category: MedicineCategory
    dosage: str  # e.g., "500mg", "10ml"
    form: str  # e.g., "tablet", "syrup", "injection"
    description: Optional[str] = None
    prescription_required: PrescriptionRequired = PrescriptionRequired.NO
    price: float
    unit: str  # e.g., "per tablet", "per bottle"
    manufacturer: Optional[str] = None
    active_ingredients: List[str] = []
    side_effects: List[str] = []
    interactions: List[str] = []  # Medicine names that interact
    storage_instructions: Optional[str] = None
    is_available: bool = True


class MedicineCreate(MedicineBase):
    """Medicine creation model"""
    sku: str  # Stock Keeping Unit


class MedicineUpdate(BaseModel):
    """Medicine update model"""
    name: Optional[str] = None
    price: Optional[float] = None
    is_available: Optional[bool] = None
    description: Optional[str] = None


class MedicineInDB(MedicineBase):
    """Medicine in database model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    sku: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    times_ordered: int = 0
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class Medicine(MedicineBase):
    """Medicine response model"""
    id: str
    sku: str
    created_at: datetime
    times_ordered: int
    
    class Config:
        from_attributes = True


class MedicineAlternative(BaseModel):
    """Alternative medicine suggestion"""
    medicine_id: str
    name: str
    reason: str  # Why it's an alternative
    price_difference: float


class MedicineSearch(BaseModel):
    """Medicine search query"""
    query: str
    category: Optional[MedicineCategory] = None
    max_price: Optional[float] = None
    prescription_required: Optional[PrescriptionRequired] = None
    limit: int = 20


class ParsedMedicine(BaseModel):
    """Parsed medicine from natural language"""
    name: str
    dosage: Optional[str] = None
    quantity: int = 1
    confidence: float = 0.0
    alternatives: List[str] = []
