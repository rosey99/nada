import logging
import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
#from pydantic_ai.models.openai import OpenAIModel  # noqa: F401
from contextlib import asynccontextmanager
from nada.fastapi_agent.fastapi_agent import FastAPIAgent
from nada.llm.locals import get_available_llama_models, get_llama_model
from nada.simple_agent import ProviderCollection, LOCAL_PROVIDERS
from nada.models import ModelProvider

from pydantic_ai.common_tools.web_fetch import web_fetch_tool
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai_harness import Shell, FileSystem
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
load_dotenv()

logger = logging.getLogger("uvicorn")
PARENT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))


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


templates = Jinja2Templates(directory=PARENT_DIR_PATH + "/chat_ui/templates")

# Your existing routes
@app.get("/")
async def root():
    """Welcome endpoint that returns basic API information"""
    return {"message": "Welcome to My Business API"}

# TODO take this out after updating FE to use JSON endpoint
# really just for template setup testing
@app.get("/providers", response_class=HTMLResponse, tags=["providers"])
async def list_model_providers(request: Request):
    """
    Retrieve model providers and models as an html fragment. Deprecated.
    """
    providers_list = list(providers.providers.values())
    return templates.TemplateResponse(
            request=request, name="providers.html", context={"providers": providers_list}
        )
    #return list(providers.providers.values())

@app.get("/providers_json", response_model=List[ModelProvider], tags=["providers_json"])
async def json_model_providers(request: Request):
    """
    Retrieve model providers and models as JSON.

    """
    #providers_list = list(providers.providers.values())
    # return templates.TemplateResponse(
    #         request=request, name="providers.html", context={"providers": providers_list}
    #     )
    return list(providers.providers.values())


providers = ProviderCollection(provider_list=LOCAL_PROVIDERS)

if __name__ == "__main__":
    # # create model for ollama server
    # model = OpenAIModel(
    #     "ollama3.2:3d",
    #     base_url="http://localhost:11434/v1"
    # )
    #providers = ProviderCollection(provider_list=LOCAL_PROVIDERS)

    # modifies in place and returns
    providers.refresh_provider()
    provider = providers.providers['Local Llama LTV']
    provider.is_active = True

    use_model = None
    for model in provider.models:
        # get the loaded model
        if model.model_status == 'loaded':
            use_model = get_llama_model(model_id=model.id, provider=provider)
            logger.info(f'Found loaded model: {model.id}, {model.model_status}')
    if not use_model:
        model_id = 's-batman/ornith-1.0-35B-NVFP4-MTP-GGUF:MTP'
        use_model = providers.get_model_obj(model_id=model_id, provider_name=provider.name)
        # TODO consider changing the pydantic model so that models are a dict
        for model in provider.models:
           if model.id == model_id:
               model.selected = True

    model = use_model
    print("Model selected: ", model.model_id)
    # create the FastAPI Agent instance
    agent = FastAPIAgent(
        app,
        model=model,
        tools = [duckduckgo_search_tool(), web_fetch_tool(max_content_length=None)],
        capabilities=[Shell(), FileSystem()],
    )
    app.include_router(agent.router)
    app.mount("/static", StaticFiles(directory=PARENT_DIR_PATH + "/chat_ui"), name="static")
    # run the FastAPI app
    uvicorn.run(app, host="0.0.0.0", port=8000)
