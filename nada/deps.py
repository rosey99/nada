import logging

import redis.asyncio as redis
from typing import Annotated
from fastapi import Depends

from pydantic_ai.common_tools.web_fetch import web_fetch_tool
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai_harness import Shell, FileSystem

from nada.fastapi_agent.fastapi_agent import FastAPIAgent
from nada.llm.common.provider import ProviderCollection
from nada.redis.client.redis_data import red_pool
from nada.settings import providers

logger = logging.getLogger(__name__)


async def get_db() -> redis.Redis:
    """
    Gets a redis connection from the configured connection pool.
    """
    session = redis.Redis(connection_pool=red_pool)
    yield session
    await session.aclose()


def get_fastapi_agent():
    """
    Gets the FastAPI agent, all provider and model availability is
    established at startup in settings.
    """
    from nada.main import app
    selected_provider = None
    use_model = None
    for provider in providers.providers.values():
        if provider.is_active:
            selected_provider = provider
            break
    if selected_provider is None:
        raise RuntimeError("Unable to create FastAPI Agent, no valid provider found.")
    for mod_id, model in selected_provider.models.items():
        # get the loaded model
        if model.selected:
            use_model = provider.get_model(mod_id, provider=selected_provider)
            logger.info(f'Found selected model: {mod_id}, {model.model_status}')
    if not use_model:
        # This should never happen, but. . .
        model_id = list(selected_provider.models.keys())[0]
        use_model = providers.get_model_obj(model_id=model_id, provider_name=selected_provider.name)
        use_model.selected = True
        # TODO consider changing the pydantic model so that models are a dict
    logger.info(f"Model selected: {use_model.model_id}")


    # create the FastAPI Agent instance
    agent = FastAPIAgent(
        app,
        providers=providers,
        model=use_model,
        tools = [duckduckgo_search_tool(), web_fetch_tool(max_content_length=None)],
        capabilities=[Shell(), FileSystem()],
        logger=logger,
    )
    return agent


def get_model_providers() -> ProviderCollection:
    return providers

# create the deps
SessionDep = Annotated[redis.Redis, Depends(get_db)]
ProvidersDep = Annotated[ProviderCollection, Depends(get_model_providers)]
FastapiAgentDep = Annotated[FastAPIAgent, Depends(get_fastapi_agent)]
