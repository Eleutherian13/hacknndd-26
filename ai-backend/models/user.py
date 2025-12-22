from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2"""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ])
    
    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")
    
    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler):
        return {"type": "string"}


class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    username: str
    full_name: str
    phone: Optional[str] = None
    language: str = "en"  # en, de, ar
    is_active: bool = True
    is_admin: bool = False


class UserCreate(UserBase):
    """User creation model"""
    password: str


class UserUpdate(BaseModel):
    """User update model"""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    language: Optional[str] = None


class UserInDB(UserBase):
    """User in database model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    onboarding_completed: bool = False
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class User(UserBase):
    """User response model"""
    id: str
    created_at: datetime
    onboarding_completed: bool
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str  # user_id
    exp: datetime
    iat: datetime
    type: str  # access or refresh


class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str


class OnboardingData(BaseModel):
    """Onboarding questionnaire data"""
    chronic_conditions: List[str] = []
    current_medications: List[dict] = []  # [{"name": "Medicine", "frequency": "daily", "quantity": 30}]
    allergies: List[str] = []
    preferred_pharmacy: Optional[str] = None
    notification_preferences: dict = {
        "email": True,
        "sms": False,
        "whatsapp": False,
        "push": True
    }
