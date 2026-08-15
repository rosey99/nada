
from contextlib import asynccontextmanager

from fastapi import FastAPI

from nada import PARENT_DIR_PATH

import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])

# TODO this must come after logging config, move logging config
#  out to fastapi app
from nada.redis.load_lua_funcs import load_funcs
from nada.routes.agent.agent_routes import agent_router
from nada.routes.api.v1.api_routes import api_router

from fastapi.staticfiles import StaticFiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Running Example FastAPI app from "FastAPI Agent"')
    yield


# Your existing FastAPI app
app = FastAPI(
    title="Agent Management Console",
    version="1.0.0",
    description="A comprehensive LLM agent management API",
    lifespan=lifespan,
)

app.include_router(agent_router)
app.include_router(api_router)
# mount static files
app.mount("/static", StaticFiles(directory=PARENT_DIR_PATH + "/fastapi_agent/chat_ui/static"), name="static")
# initialize redis data
load_funcs()
