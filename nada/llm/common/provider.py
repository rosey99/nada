
from typing import List, Union

from nada.models import ModelProvider


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
