from pydantic import BaseModel, ConfigDict, Field, ImportString, EmailStr
from typing import Dict, Optional, List, Set, Any
#from typing_extensions import Self
import json
import uuid

from fastapi import UploadFile, Form

from pydantic_ai import RunUsage


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None

# Properties to return via API, id is always required
class User(BaseModel):
    """
    Internal User model.
    """
    username: str
    display_name: str
    is_active: int = Field(default=1, ge=0, lt=2)
    is_superuser: int = Field(default=0, ge=0, lt=2)
    email: EmailStr
    # defaults
    id: uuid.UUID = Field(description="Unique user identifier", default_factory=uuid.uuid4)
    full_name: str | None = None
    disabled: int = Field(default=0, ge=0, lt=2)


class UserPublic(BaseModel):
    """
    The public User model.
    """
    model_config = ConfigDict(extra='ignore')
    id: uuid.UUID
    display_name: str
    is_active: bool


class UserInDB(BaseModel):
    hashed_password: str
    is_active: int = Field(default=1, ge=0, lt=2)
    id: uuid.UUID = Field(description="Unique user identifier")


class APIResponse(BaseModel):
    """Model for API response data for """

    status_code: int
    data: Any
    headers: Dict[str, str]
    error: Optional[str] = None


class AgentQuery(BaseModel):
    """Request model for agent queries"""

    query: str
    history: Optional[list] = None
    files: Optional[List[UploadFile]] = None
    model_id: Optional[str] = None
    provider_slug: Optional[str] = None

    @classmethod
    def as_string(
        cls,
        agent_query: str = Form(...),
    ) -> 'AgentQuery':
        ret_val = json.loads(agent_query)
        return cls(**ret_val)


class AgentResponse(BaseModel):
    """Response model for agent queries"""

    query: str
    response: str
    status: str = "success"
    error: Optional[str] = None
    history: Optional[list] = None
    usage: Optional[RunUsage] = None

class ModelQuery(BaseModel):
    """Request model for model choice update"""

    provider_name: str
    model_id: str


class LlamaArgs(BaseModel):
    """
    Static configuration data
    """
    model_config = ConfigDict(extra='ignore')
    #
    jinja: bool = Field(description="Jinja chat templates active")
    #mmap: bool = Field(description="Memory map active", default=False)
    temperature: float = Field(description="Temperature")
    batch_size: int = Field(description="Batch size")
    ctx_size: int = Field(description="Context size")
    flash_attn: bool = Field(description="Flash attention on")

class ModelArchitecture(BaseModel):
    """

    """
    model_config = ConfigDict(extra='ignore')
    input_modalities: Set[str] = Field(description="Allowed input content types.")
    output_modalities: Set[str] = Field(description="Allowed output content types.")

class BaseModelData(BaseModel):
    """
    Base static data for known Llama.cpp models
    """
    model_config = ConfigDict(extra='ignore')
    #
    id: str = Field(description="Model ID")
    aliases: Optional[List[str]] = Field(description="Aliases for the model", default_factory=list)
    tags: Optional[List[str]] = Field(description="Tags", default_factory=list)
    owned_by: Optional[str] = Field(description="Model owner")
    created: Optional[int] = Field(description="Creation time")
    model_status: str = Field(description="Model is loaded or unloaded")
    selected: bool = Field(description="Model is selected for load and use, even if already loaded.", default=False)
    # for consistency with Openrouter standard
    context_size: int = Field(description="Model context length.")
    model_args: LlamaArgs
    architecture: ModelArchitecture

class LlamaModelData(BaseModelData):
    """
    Base static data for known Llama.cpp models
    """
    model_config = ConfigDict(extra='ignore')
    #
    id: str = Field(description="Model ID")
    aliases: Optional[List[str]] = Field(description="Aliases for the model", default_factory=list)
    tags: Optional[List[str]] = Field(description="Tags", default_factory=list)
    owned_by: Optional[str] = Field(description="Model owner")
    created: Optional[int] = Field(description="Creation time")
    model_status: str = Field(description="Model is loaded or unloaded")
    selected: bool = Field(description="Model is selected for load and use, even if already loaded.", default=False)
    # for consistency with Openrouter standard
    context_size: int = Field(description="Model context length.")
    model_args: LlamaArgs
    architecture: ModelArchitecture

class ModelProvider(BaseModel):
    """

    """
    name: str = Field(description="Provider name")
    # TODO make this a literaal or use an enum :()
    status: str = Field(description="Provider is ONLINE, OFFLINE, or unknown", default='unknown')
    is_active: bool = Field(description="Is this the currently selected provider", default=False)
    prompt_url: str = Field(description="Base URL")
    models_api_timeout: Optional[int] = Field(description="Timeout in seconds for API calls, not including chat.", default=0)
    models_url: Optional[str] | None = Field(description="Models and model status URL.")
    # load_url is here to facilitate explicitly measuring model load times, future use.
    load_url: Optional[str] | None = Field(description="Manual model loading URL")
    api_key: str = Field(description="Optional API key, required for most clients even local", default='NOT_A_REAL_KEY')
    support_autoload: Optional[bool] = Field(description="Manual model loading URL", default=True)
    models: Dict[str, LlamaModelData] = Field(description="Hosted LLMs", default_factory=dict)
    get_available_models: ImportString
    get_model: ImportString
