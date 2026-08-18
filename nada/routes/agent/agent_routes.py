from typing import Annotated, Optional
from dataclasses import asdict
from datetime import datetime, timedelta, timezone


from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic_ai import BinaryContent, RunUsage

from nada.deps import get_fastapi_agent, SessionDep
from nada.models import AgentQuery, AgentResponse, UserInDB, UserUsage, RequestUsage
from nada import security
from nada.redis.client.redis_data import redis, KVBase, red_pool
from nada.settings import settings, templates
import json
import logging
import time
import uuid

logger = logging.getLogger(__name__)

agent_router = APIRouter(prefix="/agent/v1", tags=["agent"])


@agent_router.get("/login", response_class=HTMLResponse)
async def get_login_user(request: Request): #, accept_language: str = Depends(get_accept_language)):
    #logger.debug('Got the item request')
    #logger.debug(f'Got the item request for locale: {request.headers.get("Accept-Language", None)}')
    # this_locale = request.headers.get("Accept-Language", None)
    # lang = 'en'
    # if this_locale:
    #     lang = this_locale[:2]
    #     if lang in TRANSLATIONS:
    #         this_trans = TRANSLATIONS[lang]
    #     else:
    #         this_trans = None
    # #logger.debug(f'jinja is using: {type(TRANSLATIONS)}')
    # #templates.env.install_gettext_translations([lang])
    # if this_trans:
    #     templates.env.install_gettext_translations(this_trans)
    return templates.TemplateResponse(
        request=request, name="login.html", context={}
    )

@agent_router.post("/login/authorize", response_class=HTMLResponse)
async def authenticate(session: SessionDep, request: Request, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await security.authenticate_user(
        db=session, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect ID or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_token = security.create_access_token(user.username, expires_delta=access_token_expires)
    #token = Token(access_token=new_token)
    response = RedirectResponse(status_code=303, url='/agent/v1/chat')
    response.set_cookie(key=settings.COOKIE_NAME, value=f"Bearer {new_token}") #, httponly=True)
    #logger.info(f"Authenticated user: {user.id.hex}")
    # token_header = f'{token.token_type} {token.access_token}'
    # headers = {'Authorization': token_header}
    return response

@agent_router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, current_user: security.CurrentCookieUser):
    """
    Main chat page.
    """
    if isinstance(current_user, UserInDB):
        context = {'APP_TITLE': "Nada Agent Chat", "current_user": current_user}
        return templates.TemplateResponse(
                request=request, name="index.html", context=context
            )
    else:
        return current_user


@agent_router.post("/query", response_model=AgentResponse)
async def query_ai_agent(request: Request,
                         session: SessionDep,
                         current_user: security.CurrentCookieUser,
                         agent_query: Annotated[AgentQuery, Depends(AgentQuery.as_string)],
                         files: list[UploadFile] | None = None):
    """
    Ask the AI agent about available API endpoints and how to use them.
    The agent can help you understand what each endpoint does and how to call it.
    """
    if isinstance(current_user, security.CredentialsException) or current_user is None:
        raise security.CredentialsException
    agent = get_fastapi_agent(app=request.app, agent_query=agent_query)
    # TODO session test for persistence dep
    #   and file handling
    #r = await session.set('test123', 'test')
    #r = await session.get('test123')
    #logger.info(f'deps test: {r}')
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
                # TODO mucho
                #  external mime-type handlers, needs granular and total control
                #
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

    thread_id = "default"
    if agent_query.thread_id is not None:
        thread_id = agent_query.thread_id
    logger.info(f"Saving thread: {thread_id}")

    # save history to thread
    red_con = redis.Redis(connection_pool=red_pool)
    kv = KVBase(redis_con=red_con, service_prefix=f"thread_{current_user.username}")
    _ = await kv.add_service_keys(service_name=thread_id, keys=["messages"], values=[json.dumps(history)])
    try:
        start_time = time.time()
        response, history, usage = await agent.chat(agent_query.query, bin_content=bin_files, history=history)
        end_time = time.time()
        # TODO this may not be necessary, in case of time out for long requests
        red_con = redis.Redis(connection_pool=red_pool)
        kv = KVBase(redis_con=red_con, service_prefix=f"thread_{current_user.username}")
        _ = await kv.add_service_keys(service_name=thread_id, keys=["messages"], values=[json.dumps(history)])
        elapsed_time = end_time - start_time
        usage_count = await record_usage(
            session=red_con,
            current_user=current_user,
            usage_id=uuid.uuid4().hex,
            usage_data=usage,
            elapsed_time=elapsed_time,
            model_id=agent_query.model_id,
            provider_slug=agent_query.provider_slug
        )
        logger.info(f"Recorded {usage_count} usage items, elapsed time: {elapsed_time}")
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
        raise
        return AgentResponse(
            query=agent_query.query,
            response="",
            status="error",
            error=str(e),
            history=history,
        )

async def record_usage(
    session: redis,
    current_user: UserInDB,
    usage_id: str,
    usage_data: RunUsage, elapsed_time: float,
    model_id: str,
    provider_slug: str
):
    red_con = session #(db=settings.REDIS_DATA_DBNUM)

    usage_data = asdict(usage_data)

    # TODO this is messy, but upstream changes in RunUsage
    #  which permit None for certain stats break redis
    #  likewise for 'details' which would require serialization
    #  this needs its own dedicated model to auto ignore/coerce values
    usage_data.pop('details')
    usage_data = {k: 0 if v is None else v for k, v in usage_data.items()}
    usage_data['elapsed_time'] = elapsed_time
    usage_data['model_id'] = model_id
    usage_data['provider_slug'] = provider_slug
    unique_key = f"usage:{current_user.username}:{usage_id}"
    logger.info(f"Usage data: {usage_data}")
    r = await red_con.hset(unique_key, mapping=usage_data)
    time_score = time.time()

    _ = await red_con.zadd("usage", {unique_key: time_score})
    _ = await red_con.zadd(f"usage:{current_user.username}", {unique_key: time_score})
    #_ = await red_con.zadd(unique_key, {f"{current_user.username}": time.time()})
    return r
