#from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from fastapi.templating import Jinja2Templates

from nada import PARENT_DIR_PATH, ROOT_DIR_PATH
from nada.llm.common.provider import ProviderCollection

import json


def load_providers():
    config_path = settings.PROVIDER_CONFIG_PATH
    if not config_path.startswith('/'):
        # load it relative to the project directory
        config_path = ROOT_DIR_PATH + '/' + config_path
    with open(config_path, 'r') as conf_file:
        conf = conf_file.read()
    provider_config = json.loads(conf)
    # Hydrate the raw provider onfig with API key(s)
    for provider in provider_config:
        if provider.get("api_key") is not None:
            provider["api_key"] = getattr(settings, provider["api_key"])
    providers = ProviderCollection(provider_list=provider_config)
    if settings.PROVIDER_DEFAULT:
        providers.providers[settings.PROVIDER_DEFAULT].is_active = True
    return providers


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file='.env',
        env_ignore_empty=True,
        extra="ignore",
    )
    log_level: str = Field(default="info", description="Logging level")
    #model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    PROVIDER_CONFIG_PATH: str
    CELERY_RESULT_URI: str
    CELERY_BROKER_URI: str
    REDIS_CACHE_HOST: str
    REDIS_CACHE_PORT: int
    REDIS_CACHE_DBNUM: int
    REDIS_DATA_HOST: str
    REDIS_DATA_PORT: int
    REDIS_DATA_DBNUM: int
    # providers
    PROVIDER_CONFIG_PATH: str
    PROVIDER_DEFAULT: str | None = None
    # optional
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = None
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: str | None = None
    OPENROUTER_API_KEY: str | None = None



settings = Settings()

templates = Jinja2Templates(directory=PARENT_DIR_PATH + "/fastapi_agent/chat_ui/templates")

providers = load_providers()
