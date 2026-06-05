from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
from typing import Optional

class MongoDBConnection:
    """MongoDB connection wrapper"""
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

mongo_conn: MongoDBConnection = MongoDBConnection()

async def connect_mongodb() -> None:
    """Connect to MongoDB and initialize database connection"""
    mongo_conn.client = AsyncIOMotorClient(settings.MONGO_URL)
    mongo_conn.db = mongo_conn.client[settings.MONGO_DB_NAME]
    print(f"Connected to MongoDB: {settings.MONGO_DB_NAME}")

async def close_mongodb() -> None:
    """Close MongoDB connection gracefully"""
    if mongo_conn.client:
        mongo_conn.client.close()
        print("Closed MongoDB connection")

async def get_mongodb() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance for dependency injection"""
    return mongo_conn.db
