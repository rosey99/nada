from typing import List

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file='.env',
        env_ignore_empty=True,
        extra="ignore",
    )
    log_level: str = Field(default="info", description="Logging level")
    #model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    CELERY_RESULT_URI: str
    CELERY_BROKER_URI: str
    REDIS_CACHE_HOST: str
    REDIS_CACHE_PORT: int
    REDIS_CACHE_DBNUM: int
    REDIS_DATA_HOST: str
    REDIS_DATA_PORT: int
    REDIS_DATA_DBNUM: int

settings = Settings()
