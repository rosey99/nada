import logging

import requests

from typing import List, Union

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from nada.models import LlamaArgs, LlamaModelData, ModelProvider

logger = logging.getLogger(__name__)

class ProviderCollection:
    """

    """
    def __init__(self, provider_list: List[dict]):

        # TODO for now validate here in init
        self.providers = {provider['name']: ModelProvider(**provider) for provider in provider_list}

    def get_model_list(self, provider_name: str):
        provider = self.providers[provider_name].get_available_models(self.providers[provider_name])
        self.providers[provider_name] = provider
        return provider

    def get_model_obj(self, model_id: str, provider_name: str):
        model_obj = self.providers[provider_name].get_model(model_id, self.providers[provider_name])
        return model_obj

    def refresh_provider(self, provider_name: Union[str, None] = None):
        provider_names = self.providers.keys() if provider_name is None else [provider_name]
        for provider in provider_names:
            _ = self.get_model_list(provider)



def get_llama_model(model_id: str, provider: ModelProvider) -> OpenAIChatModel:
    """
    Get a local llama.cpp model
    """
    model = OpenAIChatModel(
        model_id,
        provider=OpenAIProvider(
            base_url=provider.prompt_url,
            api_key=provider.api_key,
        ),
        #settings = ModelSettings(thinking=False)
    )
    return model


def get_available_llama_models(provider: ModelProvider) -> ModelProvider:
    """

    """
    #raw_provider = provider.model_dump()
    url = f"{provider.models_url}"  # noqa E501
    #print('URL: ', url)
    headers = {}
    response = requests.get(url) #, headers=headers)
    #res = response.json()
    #print(res)
    model_list = response.json()['data']
    num_models = len(model_list)
    new_models = []
    arg_prefix = '--'
    for model in model_list:
        try:
            args = model['status']['args']
            status = model['status']['value']
            # convert args from list to dict suitable for validation
            argcount = len(args)
            new_args = {}
            key = 'no_key'
            for i in range(argcount):
                next = i + 1
                if args[i].startswith(arg_prefix):
                    key = args[i][2:].replace('-', '_')
                    new_args[key] = args[next] if next < argcount \
                    and not args[next].startswith(arg_prefix) else True
        except KeyError as e:
            logger.error(f'A parsing error occured: \n{str(e)}')
        except Exception as e:
            logger.error(f'An exit error occured: \n{str(e)}')
            raise  # reraise
        args_obj = LlamaArgs(**new_args)
        model_obj = LlamaModelData(model_status=status,
            context_size=args_obj.ctx_size,
            model_args=args_obj,
            **model
        )

        new_models.append(model_obj)

    provider.models = new_models
    return provider
