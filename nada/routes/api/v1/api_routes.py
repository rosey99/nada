from typing import Dict

from fastapi import APIRouter, Request

from nada.models import ModelProvider
from nada.deps import ProvidersDep

api_router = APIRouter(prefix="/api/v1")

# TODO existing routes
@api_router.get("/")
async def root():
    """Welcome endpoint that returns basic API information"""
    return {"message": "Welcome to My Business API"}


@api_router.get("/providers", response_model=Dict[str, ModelProvider], tags=["providers"])
async def json_model_providers(request: Request, providers: ProvidersDep):
    """
    Retrieve model providers and models as JSON.

    """
    # leaving request here for now, auth to follow
    return providers.providers
