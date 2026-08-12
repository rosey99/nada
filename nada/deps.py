import logging

import redis.asyncio as redis
from typing import Annotated
from fastapi import Depends, FastAPI

from pydantic_ai.common_tools.web_fetch import web_fetch_tool
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai_harness import Shell, FileSystem

from nada.fastapi_agent.fastapi_agent import FastAPIAgent
from nada.llm.common.provider import ProviderCollection
from nada.models import AgentQuery
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


def get_fastapi_agent(app: FastAPI, agent_query: AgentQuery):
    """
    Gets the FastAPI agent, all provider and model availability is
    established at startup in settings.
    """
    selected_provider = None
    selected_slug = None
    use_model = None
    model_id = None
    if agent_query.provider_slug is not None:
        selected_provider = providers.providers.get(agent_query.provider_slug, None)
        selected_slug = agent_query.provider_slug
    else:
        # Find the active provider
        for slug, provider in providers.providers.items():
            if provider.is_active:
                selected_provider = provider
                selected_slug = slug
                break
        logger.info(f'Auto-selected active provider: {selected_slug}')
    if selected_provider is None:
        raise RuntimeError("Unable to create FastAPI Agent, no valid provider found.")
    # Done with provider validation, get actual model and model_data
    model_data = None
    if agent_query.model_id is not None:
        model_data = selected_provider.models.get(agent_query.model_id, None)
        if model_data:
            use_model = providers.get_model_obj(model_id=model_data.id, provider_slug=selected_slug)
    else:
        for model_id, model in selected_provider.models.items():
            # get the loaded model
            if model.selected:
                model_data = model
                use_model = provider.get_model(model_id, provider=selected_provider)
                logger.info(f'Found selected model: {model_id}, {model.model_status}')
    if not use_model:
        # This should never happen, but. . .
        model_id = list(selected_provider.models.keys())[0]
        model_data = selected_provider.models[model_id]
        use_model = providers.get_model_obj(model_id=model_id, provider_slug=selected_slug)
        selected_provider.models[model_id].selected = True
        logger.info(f"Auto selected model for active provider: {use_model.id}")
    if not model_data or not use_model:
        # This should never occur
        raise RuntimeError(f"Unable to load model for provider {selected_provider.name} with slug: {selected_slug} and model: {model_id}")
    # create the FastAPI Agent instance
    agent = FastAPIAgent(
        app,
        # TODO providers can go now
        providers=providers,
        model=use_model,
        model_data=model_data,
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
#FastapiAgentDep = Annotated[FastAPIAgent, Depends(get_fastapi_agent)]
