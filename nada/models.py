from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Set

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

class ModelProvider(BaseModel):
    """

    """
    name: str = Field(description="Provider name")
    prompt_url: str = Field(description="Base URL")
    models_url: Optional[str] | None = Field(description="Models and model status URL")
    load_url: Optional[str] | None = Field(description="Manual model loading URL")
    support_autoload: Optional[bool] = Field(description="Manual model loading URL", default=True)

class LlamaArgs(BaseModel):
    """
    Static configuration data
    """
    model_config = ConfigDict(extra='ignore')
    #
    jinja: bool = Field(description="Model ID")
    mmap: bool = Field(description="Memory map active")
    temperature: float = Field(description="Temperature")
    batch-size: int = Field(description="Batch size")
    ctx-size: int = Field(description="Context size")
    flash-attn: bool = Field(description="Flash attention on")


class LlamaModelData(BaseModel):
    """
    Base static data for known Llama.cpp models
    """
    model_config = ConfigDict(extra='ignore')
    #
    id: str = Field(description="Model ID")
    aliases: Optional[Set[str]] = Field(description="Aliases for the model", default_factory=set)
    tags: Optional[Set[str]] = Field(description="Tags", default_factory=set)
    owned_by: Optional[str] = Field(description="Model owner")
    created: Optional[int] = Field(description="Creation time")
    status: str = Field(description="Model is loaded or unloaded")
    args: LlamaArgs
