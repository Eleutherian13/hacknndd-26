from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    # Project
    PROJECT_NAME: str = "Mediloon AI Pharmacy"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    
    # Database
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "mediloon"
    REDIS_URL: str
    
    # AI/ML
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str = ""
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_PROJECT: str = "mediloon-pharmacy"
    
    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Integrations
    N8N_WEBHOOK_URL: str = ""
    ZAPIER_WEBHOOK_URL: str = ""
    CMS_WEBHOOK_URL: str = ""
    
    # Email
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@mediloon.com"
    SENDGRID_FROM_NAME: str = "Mediloon Pharmacy"
    
    # SMS
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    TWILIO_WHATSAPP_NUMBER: str = ""
    
    # Agent Configuration
    AGENT_TEMPERATURE: float = 0.7
    AGENT_MAX_TOKENS: int = 1000
    AGENT_MODEL: str = "gpt-4-turbo-preview"
    
    # Prediction
    PREDICTION_MIN_ORDERS: int = 3
    PREDICTION_CONFIDENCE_THRESHOLD: float = 0.7
    PREDICTION_DAYS_AHEAD: int = 30
    
    # Feature Flags
    ENABLE_VOICE_ORDERING: bool = True
    ENABLE_PREDICTIVE_ORDERING: bool = True
    ENABLE_AUTO_PROCUREMENT: bool = True
    ENABLE_MULTI_LANGUAGE: bool = True
    SUPPORTED_LANGUAGES: str = "en,de,ar"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
