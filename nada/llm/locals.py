import logging

import requests

#from typing import List, Union

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from nada.models import LlamaArgs, LlamaModelData, ModelProvider

logger = logging.getLogger(__name__)


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
    url = f"{provider.models_url}"  # noqa E501
    #print('URL: ', url)
    response = requests.get(url, timeout=provider.models_api_timeout)
    #res = response.json()
    #print(res)
    model_list = response.json()['data']
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
