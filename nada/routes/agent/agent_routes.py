from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse

from pydantic_ai import BinaryContent

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
    # File/attachment handling
    bin_files = []
    if files is not None:
        files_by_type = {}
        file_count = len(files)
        logger.info(f"Got {file_count} files")
        for i in range(file_count):
            logger.info(f"Got file {files[i].filename}")
            logger.info(f"File is {files[i].size} bytes")
            logger.info(f"File type is {files[i].content_type}")
            files_of_type = files_by_type.setdefault(files[i].content_type, [])
            files_of_type.append(files[i])
        # TODO attachment types and conversions probably wants dedicated callable(s)
        allowed_modalities = agent.model_data.architecture.input_modalities  # a set()
        file_types = {k.split('/')[0] for k in files_by_type}
        not_supported = file_types - allowed_modalities
        if not_supported:
           logger.error(f"Unsupported uploaded file types: {not_supported}")
           # remove bad types, basic version
           for bad_type in not_supported:
               for k in files_of_type:
                   if k.startswith(bad_type):
                       del files_by_type[k]
                       logger.info(f"Removing unsupported file type: {k}")
        # Just add the raw content to the query for now
        for k, v in files_by_type.items():
            logger.info(f'Adding file(s) to agent query: {", ".join(f.filename for f in v)}')
            for file in v:
                agent_query.query += f"\nAttached file: {file.filename}\n"
                if k.startswith("text"):
                    raw = await file.read()
                    bin_content  = BinaryContent(data=raw, media_type=k)
                    bin_files.append(bin_content)
                else:
                    bin_data = await file.read()
                    bin_content = BinaryContent(data=bin_data, media_type=k)
                    bin_files.append(bin_content)
    #
    history = agent_query.history
    try:
        response, history, usage = await agent.chat(agent_query.query, bin_content=bin_files, history=history)
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
