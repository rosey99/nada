import redis.asyncio as redis
from typing import Annotated
from fastapi import Depends

from nada.redis.client.redis_data import red_pool

async def get_db() -> redis.Redis:
    session = redis.Redis(connection_pool=red_pool)
    yield session
    await session.aclose()

SessionDep = Annotated[redis.Redis, Depends(get_db)]
