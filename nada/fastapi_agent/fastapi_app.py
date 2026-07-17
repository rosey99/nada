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

# Mock database
users_db = [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "age": 30},
    {"id": 2, "name": "Bob", "email": "bob@example.com", "age": 25},
]


# Example Pydantic models
class User(BaseModel):
    name: str
    email: str
    age: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    age: Optional[int] = None


templates = Jinja2Templates(directory=PARENT_DIR_PATH + "/chat_ui/templates")

# Your existing routes
@app.get("/")
async def root():
    """Welcome endpoint that returns basic API information"""
    return {"message": "Welcome to My Business API"}


@app.get("/providers", response_class=HTMLResponse, tags=["providers"])
async def list_model_providers(request: Request):
    """
    Retrieve a list of users with pagination.
    This endpoint allows you to get multiple users at once.
    """
    providers_list = list(providers.providers.values())
    return templates.TemplateResponse(
            request=request, name="providers.html", context={"providers": providers_list}
        )
    #return list(providers.providers.values())

@app.get("/providers_json", response_model=List[ModelProvider], tags=["providers_json"])
async def json_model_providers(request: Request):
    """
    Retrieve a list of users with pagination.
    This endpoint allows you to get multiple users at once.
    """
    #providers_list = list(providers.providers.values())
    # return templates.TemplateResponse(
    #         request=request, name="providers.html", context={"providers": providers_list}
    #     )
    return list(providers.providers.values())

@app.get("/users/{user_id}", response_model=UserResponse, tags=["users"])
async def get_user(user_id: int):
    """
    Get a specific user by their unique ID.
    Returns detailed information about a single user.
    """
    global users_db
    user = [u for u in users_db if u["id"] == user_id][0]
    return user


@app.post("/users", response_model=UserResponse, tags=["users"])
async def create_user(user: User):
    """
    Create a new user in the system.
    Provide name, email, and optionally age to create a user account.
    """
    global users_db

    # Mock creation - replace with your actual database logic
    new_user = {"id": (len(users_db) + 1), **user.model_dump()}
    users_db.append(new_user)
    return new_user


@app.put("/users/{user_id}", response_model=UserResponse, tags=["users"])
async def update_user(user_id: int, user: dict):
    """
    Update an existing user's information.
    All fields can be modified using this endpoint.
    """
    global users_db

    _user = [u for u in users_db if u["id"] == user_id][0]
    _user.update(user)
    return _user


@app.delete("/users/{user_id}", tags=["users"])
async def delete_user(user_id: int):
    """
    Delete a user from the system.
    This action cannot be undone.
    """
    global users_db

    users_db = [user for user in users_db if user["id"] != user_id]
    return {"message": f"User {user_id} has been deleted"}

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
        #if model.model_status == 'loaded':
        #    use_model = get_llama_model(model_id=model.id, provider=provider)
            #print('Found loaded model: ', model.id, model.model_status)
            #print(f'Context: {model.context_size}')
        pass
    if not use_model:
        use_model = providers.get_model_obj(model_id='s-batman/ornith-1.0-35B-NVFP4-MTP-GGUF:MTP', provider_name=provider.name)

    model = use_model
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
