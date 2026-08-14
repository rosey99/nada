from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from fastapi.templating import Jinja2Templates
from slugify import slugify

from nada import PARENT_DIR_PATH, ROOT_DIR_PATH

from nada.llm.common.provider import ProviderCollection

import logging
import json


logger = logging.getLogger(__name__)


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
    providers.refresh_provider()
    selected_provider = None
    selected_model = None
    if settings.PROVIDER_DEFAULT:
        try:
            def_provider = providers.providers[slugify(settings.PROVIDER_DEFAULT)]
        except KeyError:
            raise RuntimeError(f"Invalid default provider: {settings.PROVIDER_DEFAULT}, verify provider configuration at {config_path}")
        if len(def_provider.models) > 0:  # provider is offline
            selected_provider = def_provider
            selected_provider.is_active = True
            if settings.PROVIDER_MODEL_DEFAULT:
                # TODO, once again. . .make this a dict
                for mod_id, model in selected_provider.models.items():
                    if mod_id == settings.PROVIDER_MODEL_DEFAULT:
                        model.selected = True
                        selected_model = mod_id
            else:
                # get the first model
                mod_id = list(selected_provider.models.keys())[0]
                selected_model = selected_provider.models[mod_id]
                print(f"Selected first available model for provider {settings.PROVIDER_DEFAULT}")
        else:
            # TODO add logging
            print("Default provider has 0 models available")
            # get the first availble provider with a valid model, or exit
            selected_provider = None
    if selected_provider is None:
        # try to get the first availble provider with a valid model, or exit
        for name, provider in providers.providers.items():
            if len(provider.models) > 0:
                selected_provider = provider
                selected_model = selected_provider.models[0]
                selected_model.selected = True
                break
    if selected_provider is None:
        raise RuntimeError(f"No valid provider and model configuration found at {config_path}")
    return providers


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./nada/)
        #  ignored in default compose/docker setup
        #  which uses env vars instead
        env_file= ROOT_DIR_PATH + '/.env',
        env_ignore_empty=True,
        extra="ignore",
    )
    log_level: str = Field(default="info", description="Logging level")
    DEFAULT_TENANT: str = "nada"
    COOKIE_NAME: str = "access_token"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = 'HS256'
    #
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
    PROVIDER_MODEL_DEFAULT: str | None = None
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
