"""Global pytest configuration and shared fixtures."""

import os
import sys
from pathlib import Path

import pytest
import redis

from nada.redis.client.redis_data import KVBase
from nada.redis.load_lua_funcs import load_funcs
from nada.settings import settings

# Ensure the project root is on the path so imports work
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture
def kvbase(redis_client: redis.Redis):
    """A KVBase instance backed by the test Redis client."""
    return KVBase(redis_con=redis_client, service_name="test_svc")

@pytest.fixture
def redis_client():
    """Redis client fixture for integration tests using database 15."""
    client = redis.Redis(
        host=settings.REDIS_DATA_HOST,
        port=settings.REDIS_DATA_PORT,
        db=15,
    )
    # always start with a clean db
    client.flushdb()
    load_funcs()
    yield client
    client.flushdb()
    client.close()

@pytest.fixture
def kvstore(redis_client: redis_client):
    """A KVBase instance backed by the test Redis client."""
    return KVBase(redis_con=redis_client, service_prefix="test_svc")
