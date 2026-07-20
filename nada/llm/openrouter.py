import logging

import httpx
import requests

from enum import Enum

#from langchain_openrouter import ChatOpenRouter
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Set
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

from nada.models import ModelProvider, ModelArchitecture


logger = logging.getLogger(__name__)

class OpenRouterSortOrder(str, Enum):
    throughput = 'throughput-high-to-low'
    context = 'context-high-to-low'
    latency = 'latency-low-to-high'
    intelligence = 'intelligence-high-to-low'

class OpenRouterModelListArgs(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    max_price: float = Field(
        description="The maximum price to include in model listing.",
        default=0.0
    )
    sort_order: OpenRouterSortOrder = Field(
        description="The sort order for the OpenRouter model listing.",
        default='throughput-high-to-low'
    )


# TODO needs available parms, e.g. temp, etc.
class OpenRouterModelArgs(BaseModel):
    """

    """
    pass

# TODO class name is taken :() rename this and unify with a std
class MyOpenRouterModel(BaseModel):
    model_config = ConfigDict(extra='ignore')
    id: str = Field(description="The OpenRouter model id.")
    name: str = Field(description="The model's friendly name.")
    description: str = Field(description="Model description.")
    context_length: int = Field(description="Maximum model context length per session.")
    aliases: Optional[List[str]] = Field(description="Aliases for the model", default_factory=list)
    tags: Optional[List[str]] = Field(description="Tags", default_factory=list)
    created: Optional[int] = Field(description="Creation time")
    model_status: str = Field(description="Model is loaded or unloaded", default='loaded')
    # TODO fix model_args with a real model? Probably will not use it.
    model_args: dict | None = None
    reasoning: dict | None = None
    supported_parameters: Set[str] | None = None
    knowledge_cutoff: str | None = None
    expiration_date: str | None = None
    architecture: ModelArchitecture


class OpenRouterModels(BaseModel):
    model_config = ConfigDict(extra='ignore')
    count: int = Field(
        description="The count of currently available models."
    )
    models: List[MyOpenRouterModel] = Field(
        description="Listing of currently available models."
    )


def get_available_openrouter_models(provider: ModelProvider) -> ModelProvider:
    """
    A placeholder for now
    """
    args = OpenRouterModelListArgs()  # TODO fix this to allow for default overrides from settings
    # TODO fix this BS, move to config file
    url = f"https://openrouter.ai/api/v1/models?max_price={args.max_price}&sort={args.sort_order}"  # noqa E501
    headers = {"Authorization": f"Bearer {provider.api_key}"}
    api_timeout = provider.models_api_timeout
    response = requests.get(url, headers=headers, timeout=api_timeout)
    #res = response.json()
    #print(response.text)
    model_list = response.json()['data']
    logger.info(f'Found {len(model_list)} available Openrouter models')
    new_models = []
    for model in model_list:
        model_obj = MyOpenRouterModel(**model)
        print(model_obj.architecture.model_dump())
        new_models.append(model_obj)
    provider.models = new_models
    return provider


def get_openrouter_model(model_id: str, provider: ModelProvider) -> OpenRouterModel:
    """

    """
    model = OpenRouterModel(
        model_id,
        provider=OpenRouterProvider(
            api_key=provider.api_key,
            http_client=httpx.AsyncClient(timeout=None),
        ),
    )
    return model
