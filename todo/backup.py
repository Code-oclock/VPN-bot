import redis.asyncio as redis

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)

async def save_user_data(user_id: int, key: str, value: str):
    await redis_client.set(f"user:{user_id}:{key}", value)

async def get_user_data(user_id: int, key: str) -> str:
    return await redis_client.get(f"user:{user_id}:{key}")

async def delete_user_data(user_id: int, key: str):
    await redis_client.delete(f"user:{user_id}:{key}")

