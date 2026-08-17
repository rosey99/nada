from typing import Annotated, Any, Dict, List
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Request, Depends
from datetime import datetime, timedelta

from pydantic_ai import RunUsage

from nada.models import ModelProvider, Token, User, UserInDB, UserUsage
from nada.deps import ProvidersDep, SessionDep
from nada.security import CredentialsException, authenticate_user, create_access_token, get_current_active_user
from nada.settings import settings
from nada.redis.client.redis_data import KVBase
import json
import time
import uuid

import logging
logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/api/v1", tags=["api-v1"])

# TODO existing routes
@api_router.get("/")
async def root():
    """Welcome endpoint that returns basic API information"""
    return {"message": "Welcome to My Business API"}


@api_router.get("/providers", response_model=Dict[str, ModelProvider])
async def json_model_providers(request: Request, providers: ProvidersDep, current_user: Annotated[UserInDB, Depends(get_current_active_user)]):
    """
    Retrieve model providers and models as JSON.

    """
    # leaving request here for now, auth to follow
    return providers.providers


@api_router.get("/usage", response_model=UserUsage)
async def get_user_usage(
    request: Request,
    session: SessionDep,
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
    since_time: float | None = None) -> UserUsage:
    """
    Gets user usage as a list of objects.
    """
    if isinstance(current_user, UserInDB):
        #red = SessionDep(db=settings.REDIS_DATA_DBNUM)
        if not since_time:
            since_time = time.time() - 36000  # ten hours
        result = await get_usage(session=session, current_user_name=current_user.username, since_time=since_time)
    return result



@api_router.get("/threads", response_model=Dict[str, Dict[str, Any]])
async def get_user_thread(request: Request, session: SessionDep, current_user: Annotated[UserInDB, Depends(get_current_active_user)], thread_id: str | None = None):
    """
    Gets a user thread. These are saved histories, with the 'default' thread saved per request
    both before and after agent invocation automatically.
    """
    if isinstance(current_user, UserInDB):
        red = SessionDep(db=settings.REDIS_DATA_DBNUM)
        kv = KVBase(redis_con=red, service_prefix=f"thread_{current_user.username}")
        service_names = await kv.get_services()  # a set()
        if thread_id:
            if thread_id not in service_names:
                logger.info(f"Requested thread: {thread_id} does not exist")
                return {}
            service_names = [thread_id]
        result = {}
        for s_name in service_names:
            result[s_name] = await kv.get_service_all(s_name)
        return result
    return current_user


@api_router.delete("/threads", response_model=Dict[str, int])
async def delete_user_thread(
    request: Request,
    session: SessionDep,
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
    thread_ids: List[str] ):
    """
    Delete one or more user threads. These are saved histories, with the 'default' thread saved per request
    both before and after agent invocation automatically. The 'default' thread cannot be deleted here.
    """
    if isinstance(current_user, UserInDB):
        red = SessionDep(db=settings.REDIS_DATA_DBNUM)
        kv = KVBase(redis_con=red, service_prefix=f"thread_{current_user.username}")
        service_names = await kv.get_services()  # a set()
        real_threads = []
        if thread_ids:
            for thread_id in thread_ids:
                if thread_id not in service_names:
                    logger.info(f"Requested thread: {thread_id} does not exist")
                    continue
                if thread_id == "default":
                    logger.info("Not allowed to delete default thread, skipping")
                    continue
                real_threads.append(thread_id)
            if not real_threads:
                logger.info("No threads found for deletee")
                return {}
            #service_names = [thread_id]
        logger.info(f"Deleting thread(s): {thread_id}")
        result = {}
        #i = 0
        for s_name in real_threads:
           result[s_name] = 0
           res = await kv.delete_service(s_name)
           logger.info(f"Got delete result: {res}")

        return result
    return current_user


@api_router.patch("/threads", response_model=Dict[str, int])
async def put_user_thread(
    request: Request,
    session: SessionDep,
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
    new_threads: Dict[str, list[str]]
):
    """
    Update all or part of user thread history
    """
    if isinstance(current_user, UserInDB):
        # TODO redis async and dDepends issue
        red = SessionDep(db=settings.REDIS_DATA_DBNUM)
        kv = KVBase(redis_con=red, service_prefix=f"thread_{current_user.username}")
        #service_names = list(new_context.keys())
        result = {}
        count = 0
        for s_name in new_threads.keys():
            logger.info(f"Got thread name for create: {s_name}")
            add_keys = ["thread_name", "thread_id", "created_at", "messages"]
            unique_id = uuid.uuid4().hex
            add_vals = [s_name, unique_id, datetime.isoformat(datetime.now()), json.dumps(new_threads[s_name])]
            upd_result = await kv.add_service_keys(service_name=unique_id, keys=add_keys, values=add_vals)
            if upd_result == b'OK':
                result[s_name] = len(add_keys)
                count += len(add_keys)
            else:
                result[s_name] = 0
        # return entire context back
        # service_names = await kv.get_services()

        # for s_name in service_names:
        #    result[s_name] = await kv.get_service_all(s_name)
        logger.debug(f"Saved context: {count} items")
        return result
    return current_user

@api_router.get("/context", response_model=Dict[str, Dict[str, Any]])
async def get_user_context(request: Request, session: SessionDep, current_user: Annotated[UserInDB, Depends(get_current_active_user)]):
    """
    Retrieve user context as JSON.

    """
    #
    if isinstance(current_user, UserInDB):
        # TODO redis async and dDepends issue
        red = SessionDep(db=settings.REDIS_DATA_DBNUM)
        kv = KVBase(redis_con=red, service_prefix=f"context_{current_user.username}")
        service_names = await kv.get_services()
        result = {}
        for s_name in service_names:
            result[s_name] = await kv.get_service_all(s_name)
        return result
    return current_user


@api_router.patch("/context", response_model=Dict[str, int])
async def put_user_context(
    request: Request,
    session: SessionDep,
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
    new_context: Dict[str, Dict[str, Any]]
):
    """
    Update all or part of user context
    """
    if isinstance(current_user, UserInDB):
        # TODO redis async and dDepends issue
        red = SessionDep(db=settings.REDIS_DATA_DBNUM)
        kv = KVBase(redis_con=red, service_prefix=f"context_{current_user.username}")
        #service_names = list(new_context.keys())
        result = {}
        count = 0
        for s_name in new_context.keys():
            add_keys = list(new_context[s_name].keys())
            add_vals = list(new_context[s_name].values())
            upd_result = await kv.add_service_keys(service_name=s_name, keys=add_keys, values=add_vals)
            if upd_result == b'OK':
                result[s_name] = len(add_keys)
                count += len(add_keys)
            else:
                result[s_name] = 0
        # return entire context back
        # service_names = await kv.get_services()

        # for s_name in service_names:
        #    result[s_name] = await kv.get_service_all(s_name)
        logger.debug(f"Saved context: {count} items")
        return result
    return current_user


@api_router.delete("/context", response_model=Dict[str, int])
async def delete_user_context(
    request: Request,
    session: SessionDep,
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
    new_context: Dict[str, Dict[str, Any]]
):
    """
    Delete all or part of user context
    """
    if isinstance(current_user, UserInDB):
        # TODO redis async and dDepends issue
        red = SessionDep(db=settings.REDIS_DATA_DBNUM)
        kv = KVBase(redis_con=red, service_prefix=f"context_{current_user.username}")
        service_names = await kv.get_services()
        new_service_names = set(new_context.keys())
        extra_names = service_names - new_service_names
        if extra_names:
            logger.info(f"Received context delete for non-existent keys {extra_names} for user: {current_user.id.hex}")
        result = {}
        new_service_names = new_service_names - extra_names
        for s_name in new_service_names:
            k_names = list(new_service_names.keys())
            res = await kv.delete_service_keys(service_name=s_name, keys=k_names)
            result[s_name] = res if res else 0
        return result
    return current_user


@api_router.post("/token")
async def login_for_access_token(
    db: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise CredentialsException
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@api_router.get("/users/me/")
async def read_users_me(
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
) -> User:
    return current_user


@api_router.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]


async def get_usage(session: SessionDep, current_user_name: str, since_time: float) -> UserUsage:
    red_con = session #(db=settings.REDIS_DATA_DBNUM)

    r = await red_con.zrangebyscore(f"usage:{current_user_name}", min=since_time, max='+inf', withscores=True)
    result = []
    logger.info(f"Got usage request: {current_user_name} since {datetime.fromtimestamp(since_time).isoformat()}")
    for k, time_stamp in r:
        usage_data = await red_con.hgetall(k)
        if not usage_data:
            continue
        # decode? these are always integers?
        usage_data = {k.decode(): int(v) if v.isalnum() else v.decode() for k, v in usage_data.items()}
        # TODO need a new cleaner version of RunUsage to combine these
        top_level_names = ["elapsed_time", "model_id", "provider_slug"]
        top_args = {}
        for name in top_level_names:
            try:
                top_args[name] = usage_data.pop(name)
            except KeyError:
                top_args[name] = None
        request_data = {'run_usage': RunUsage(**usage_data), 'created_time': time_stamp, **top_args}
        result.append(request_data)
    user_usage_data = UserUsage(user_id=current_user_name, from_time=since_time, usage_data=result)
    return user_usage_data
