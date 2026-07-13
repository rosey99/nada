import os

import requests

from enum import Enum

from langchain_openrouter import ChatOpenRouter
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Set
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

from nada.models import ModelProvider

# TODO add pydotenv and remove override in func body
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_API_KEY = "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"  # noqa E501


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


class OpenRouterModels(BaseModel):
    model_config = ConfigDict(extra='ignore')
    count: int = Field(
        description="The count of currently available models."
    )
    models: List[MyOpenRouterModel] = Field(
        description="Listing of currently available models."
    )


def get_available_openrouter_models(provider: ModelProvider) -> ModelProvider:
#def get_openrouter_models(model_listing_args: OpenRouterModelListArgs
        # TODO get the real data type for price
        #max_price: float = 0.0,
        #sort_order: str = 'throughput-high-to-low'
    #)
    """
    A placeholder for now
    """
    args = OpenRouterModelListArgs()  # TODO fix this to allow for default overrides from settings
    url = f"https://openrouter.ai/api/v1/models?max_price={args.max_price}&sort={args.sort_order}"  # noqa E501
    #print('URL: ', url)
    headers = {"Authorization": f"Bearer {provider.api_key}"}
    response = requests.get(url, headers=headers)
    #res = response.json()
    #print(response.text)
    model_list = response.json()['data']
    #num_models = len(model_list)
    #print(f"There are currently {num_models} models available in your range")
    #print("The top 5 models are:")
    #result = OpenRouterModels(count=num_models, models=model_list)
    new_models = []
    for model in model_list:
        model_obj = MyOpenRouterModel(**model)
        new_models.append(model_obj)

    provider.models = new_models
    #     if i < 5:
    #         print(model_list[i])
    #     else:
    #         break
    # print()
    return provider


def get_openrouter_model(model_id: str, provider: ModelProvider) -> ChatOpenRouter:
    #llm_args = openrouter_llm.model_dump()

    model = OpenRouterModel(
        model_id,
        provider=OpenRouterProvider(
            #base_url=provider.prompt_url,
            api_key=provider.api_key,
        ),
        #settings = ModelSettings(thinking=False)
    )
    return model
