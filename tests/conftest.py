"""Global pytest configuration and shared fixtures."""

import os
import sys
from pathlib import Path

import pytest
import redis

from nada.settings import settings

# Ensure the project root is on the path so imports work
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def redis_client():
    """Redis client fixture for integration tests using database 15."""
    client = redis.Redis(
        host=settings.REDIS_DATA_HOST,
        port=settings.REDIS_DATA_PORT,
        db=15,
    )
    yield client
    client.close()
