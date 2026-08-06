import logging

from typing import List, Union

from requests.exceptions import ConnectionError, Timeout
from slugify import slugify

from nada.models import ModelProvider

logger = logging.getLogger(__name__)

class ProviderCollection:
    """

    """
    def __init__(self, provider_list: List[dict]):

        # TODO for now validate here in init
        self.providers = {slugify(provider['name']): ModelProvider(**provider) for provider in provider_list}

    def get_model_list(self, provider_slug: str):

        provider = self.providers[provider_slug]
        try:
            provider = provider.get_available_models(self.providers[provider_slug])
            provider.status = 'ONLINE'
        except (Timeout, ConnectionError):
            # TODO clumsy, add a status to provider?
            provider.models = {}
            provider.status = 'OFFLINE'
            logger.error(f"Provider model listing timeout for: {provider.name}")
        self.providers[provider_slug] = provider
        return provider

    def get_model_obj(self, model_id: str, provider_slug: str):
        model_obj = self.providers[provider_slug].get_model(model_id, self.providers[provider_slug])
        return model_obj

    def refresh_provider(self, provider_slug: Union[str, None] = None):
        provider_slugs = self.providers.keys() if provider_slug is None else [provider_slug]
        for provider in provider_slugs:
            _ = self.get_model_list(provider)
