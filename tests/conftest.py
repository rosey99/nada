"""Global pytest configuration and shared fixtures."""

import sys
from pathlib import Path

import pytest
#import redis
import redis.asyncio as redis

from nada.redis.client.redis_data import KVBase
from nada.redis.load_lua_funcs import load_funcs
from nada.settings import Settings

# Ensure the project root is on the path so imports work
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

settings = Settings(REDIS_DATA_DBNUM=15)
load_funcs() # do this once per test run

@pytest.fixture
async def redis_client():
    """Redis client fixture for integration tests using test database from ."""
    client = redis.Redis(
        host=settings.REDIS_DATA_HOST,
        port=settings.REDIS_DATA_PORT,
        db=settings.REDIS_DATA_DBNUM,
    )
    # always start with a clean db
    await client.flushdb()
    yield client
    await client.flushdb()
    await client.aclose()

@pytest.fixture
def kvstore(redis_client: redis_client):
    """A KVBase instance backed by the test Redis client."""
    return KVBase(redis_con=redis_client, service_prefix="test_svc")
