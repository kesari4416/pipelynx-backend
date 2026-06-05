import redis.asyncio as redis
from typing import Optional
from app.core.config import settings

class RedisConnection:
    """Redis connection wrapper"""
    client: Optional[redis.Redis] = None

redis_conn: RedisConnection = RedisConnection()

async def connect_redis() -> None:
    """Connect to Redis and initialize client"""
    redis_conn.client = await redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    print(f"Connected to Redis: {settings.REDIS_URL}")

async def close_redis() -> None:
    """Close Redis connection gracefully"""
    if redis_conn.client:
        await redis_conn.client.close()
        print("Closed Redis connection")

async def get_redis() -> redis.Redis:
    """Get Redis client instance for dependency injection"""
    return redis_conn.client
