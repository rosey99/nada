from pydantic import BaseModel, ConfigDict, Field, ImportString
from typing import Callable, Optional, List, Set

class AIRequest(BaseModel):
    message: str = Field(
        ..., description="The user message to send to the AI", min_length=1
    )
    instructions: Optional[str] = Field(
        default=None, description="Optional instructions to guide the AI's behavior"
    )

class AIResponse(BaseModel):
    response: str = Field(..., description="The AI's response")
    model: str = Field(..., description="The model used to generate the response")


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

class LlamaModelData(BaseModel):
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
    # for consistency with Openrouter standard
    context_size: int = Field(description="Model context length.")
    model_args: LlamaArgs
    architecture: ModelArchitecture

class ModelProvider(BaseModel):
    """

    """
    name: str = Field(description="Provider name")
    prompt_url: str = Field(description="Base URL")
    models_url: Optional[str] | None = Field(description="Models and model status URL")
    load_url: Optional[str] | None = Field(description="Manual model loading URL")
    api_key: str = Field(description="Optional API key, required for most clients even local", default='NOT_A_REAL_KEY')
    support_autoload: Optional[bool] = Field(description="Manual model loading URL", default=True)
    models: List[LlamaModelData] = Field(description="Hosted LLMs", default_factory=list)
    get_available_models: ImportString
    get_model: ImportString
