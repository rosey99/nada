from typing import Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from nada.deps import ProvidersDep, FastapiAgentDep, SessionDep
from nada.models import AgentQuery, AgentResponse, ModelQuery, ModelProvider
from nada.settings import templates

import logging

logger = logging.getLogger(__name__)

agent_router = APIRouter(prefix="/agent/v1", tags=["agent"])


@agent_router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """
    Main chat page.
    """
    context = {'APP_TITLE': "Nada Agent Chat"}

    return templates.TemplateResponse(
            request=request, name="index.html", context=context
        )

@agent_router.post("/query", response_model=AgentResponse)
async def query_ai_agent(request: AgentQuery, agent: FastapiAgentDep, session: SessionDep):
    """
    Ask the AI agent about available API endpoints and how to use them.
    The agent can help you understand what each endpoint does and how to call it.
    """
    r = await session.get('test')
    print('deps test:', r)
    history = request.history
    if request.files:
        print(f"Got {len(request.files)} files")
    try:
        response, history, usage = await agent.chat(request.query, history)
        return AgentResponse(
            query=request.query,
            response=response,
            status="success",
            history=history,
            usage=usage
        )
    except HTTPException:
        raise
    except Exception as e:
        return AgentResponse(
            query=request.query,
            response="",
            status="error",
            error=str(e),
            history=history,
        )


@agent_router.post("/models_update", response_model=Dict[str, ModelProvider])
async def update_model(model_qry: ModelQuery, providers: ProvidersDep, agent: FastapiAgentDep):
    # TODO this is a mess, needs a refactor as import here breaks design
    #  need access to agent in update model endpoint, and that is a problem
    #  maybe add to settings object parsed from seperate yaml?
    provider = providers.providers[model_qry.provider_name]
    model = None
    logger.info(f"Update provider -> {provider.name} with {len(provider.models)} models")
    provider.get_available_models(provider)
    for m in provider.models.values():
        if m.id == model_qry.model_id:
            model = m
    if not model:
        # This should never happen
        logger.error(f"Unable to locate model: {model_qry.model_id} for provider {provider.name}")
    else:
        model = providers.get_model_obj(model_qry.model_id, model_qry.provider_name)
        agent.assistant.agent.model = model
    for k, v in providers.providers.items():
        if k != model_qry.provider_name:
            if v.is_active:
                v.is_active = False
        else:
            v.is_active = True
            for mod_id, model in v.models.items():
                if mod_id != model_qry.model_id and model.model_status == 'loaded':
                    model.model_status = 'unloaded'
                if mod_id == model_qry.model_id:
                    model.model_status = 'loaded'
                    model.selected = True
    return providers.providers
