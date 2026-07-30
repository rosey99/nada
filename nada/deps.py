import redis.asyncio as redis
from typing import Annotated
from fastapi import Depends

from nada.redis.client.redis_data import red_pool

def get_db() -> redis.Redis:
    #with Session(engine) as session:
    #    yield session
    session = redis.Redis(connection_pool=red_pool)
    yield session

SessionDep = Annotated[redis.Redis, Depends(get_db)]
