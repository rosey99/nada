from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse

from nada.deps import get_fastapi_agent, SessionDep
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
async def query_ai_agent(request: Request,
                         session: SessionDep,
                         agent_query: Annotated[AgentQuery, Depends(AgentQuery.as_string)],
                         files: list[UploadFile] | None = None):
    """
    Ask the AI agent about available API endpoints and how to use them.
    The agent can help you understand what each endpoint does and how to call it.
    """
    agent = get_fastapi_agent(app=request.app, agent_query=agent_query)
    # TODO session test for persistence dep
    #   and file handling
    r = await session.get('test')
    logger.info(f'deps test: {r}')
    logger.info(f'files test: {files}')
    if files is not None:
        file_count = len(files)
        logger.info(f"Got {file_count} files")
        for i in range(file_count):
            logger.info(f"Got file {files[i].filename}")
            logger.info(f"File is {files[i].size} bytes")
            logger.info(f"File type is {files[i].content_type}")
    #
    history = agent_query.history
    try:
        response, history, usage = await agent.chat(agent_query.query, history)
        return AgentResponse(
            query=agent_query.query,
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
