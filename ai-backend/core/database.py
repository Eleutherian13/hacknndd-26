from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from redis import asyncio as aioredis
from typing import Optional
import logging

from core.config import settings

logger = logging.getLogger(__name__)

# Database clients
mongodb_client: Optional[AsyncIOMotorClient] = None
redis_client: Optional[aioredis.Redis] = None
database: Optional[AsyncIOMotorDatabase] = None


async def init_db():
    """Initialize database connections"""
    global mongodb_client, redis_client, database
    
    try:
        # MongoDB
        logger.info(f"Connecting to MongoDB: {settings.MONGODB_URI}")
        mongodb_client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=10000)
        database = mongodb_client[settings.MONGODB_DB_NAME]
        
        # Test connection
        try:
            await mongodb_client.admin.command('ping')
            logger.info("MongoDB connected successfully")
        except Exception as mongo_err:
            logger.warning(f"MongoDB connection test failed: {str(mongo_err)}")
            logger.warning("Continuing without database - API will be limited")
        
        # Create indexes (non-critical if it fails)
        try:
            await create_indexes()
        except Exception as idx_err:
            logger.warning(f"Could not create indexes: {str(idx_err)}")
        
        # Redis
        logger.info(f"Connecting to Redis: {settings.REDIS_URL}")
        try:
            redis_client = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=10
            )
            
            # Test connection
            await redis_client.ping()
            logger.info("Redis connected successfully")
        except Exception as redis_err:
            logger.warning(f"Redis connection failed: {str(redis_err)}")
            logger.warning("Continuing without Redis - caching will be unavailable")
        
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        logger.warning("Application starting in limited mode (no database/cache)")


async def close_db():
    """Close database connections"""
    global mongodb_client, redis_client
    
    if mongodb_client:
        mongodb_client.close()
        logger.info("MongoDB connection closed")
    
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")


async def create_indexes():
    """Create database indexes"""
    if database is None:
        return
    
    try:
        # Users collection indexes
        await database.users.create_index("email", unique=True)
        await database.users.create_index("username", unique=True)
        
        # Orders collection indexes
        await database.orders.create_index("user_id")
        await database.orders.create_index("status")
        await database.orders.create_index("created_at")
        await database.orders.create_index([("user_id", 1), ("created_at", -1)])
        
        # Medicines collection indexes
        await database.medicines.create_index("name")
        await database.medicines.create_index("sku", unique=True)
        await database.medicines.create_index("category")
        
        # Predictions collection indexes
        await database.predictions.create_index("user_id")
        await database.predictions.create_index("medicine_id")
        await database.predictions.create_index([("user_id", 1), ("medicine_id", 1)], unique=True)
        await database.predictions.create_index("predicted_depletion_date")
        
        # Inventory collection indexes
        await database.inventory.create_index("medicine_id", unique=True)
        await database.inventory.create_index("quantity")
        
        # Agent logs collection indexes
        await database.agent_logs.create_index("agent_type")
        await database.agent_logs.create_index("user_id")
        await database.agent_logs.create_index("timestamp")
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {str(e)}")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    if database is None:
        raise RuntimeError("Database not initialized")
    return database


def get_redis() -> aioredis.Redis:
    """Get Redis client instance"""
    if redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return redis_client
