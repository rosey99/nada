import json
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pydantic_ai import RunContext, RunUsage, BinaryContent
from pydantic_ai.models import Model

from nada.fastapi_agent.agents import AIAgent
from nada.fastapi_agent.fastapi_discovery import FastAPIDiscovery
from nada.llm.common.provider import ProviderCollection
from nada.models import APIResponse, BaseModelData


class FastAPIAgent(FastAPIDiscovery):
    def __init__(
        self,
        app: FastAPI,
        providers: ProviderCollection,
        model_data: BaseModelData,
        base_url: str = "http://localhost:8000",
        auth: Optional[dict] = None,
        ignore_routes: Optional[list] = None,
        allow_routes: Optional[list] = None,
        model: Union[Model, str] = "openai:gpt-4.1-mini",
        agent_provider: str = "pydantic_ai",
        include_router: bool = False,
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ):
        """
        Initialize the FastAPI Agent with app context, routing configuration, Model settings, and agent provider name.

        Args:
            app (FastAPI): The FastAPI application instance to extract route information from.
            base_url (str): The base URL of the FastAPI application for documentation and interaction.
                            Defaults to "http://localhost:8000".
            auth (Optional[dict]): Optional dictionary of dependencies auth or external components relevant to the API.
                                   Support for all kind of authorizations.
                                   It will also add the dependencies to the /agent/query route.
            ignore_routes (Optional[list]): List of route paths to ignore when building the route prompt context.
            allow_routes (Optional[list]): List of route paths to allow when building the route prompt context.
            include_router (bool): add default agent routes to your FastAPI app. Defaults to False
            model (Union[Model, str]): A custom Model instance or model name string in the format "provider:model-id".
                                       If not provided, Defaults to "openai:gpt-4.1-mini".
            agent_provider (str): The name of which agent to use. Defailts to "pydantic_ai".
                                  supported agents: ["pydantic_ai"]

        Keyword Args:
            verify_api_call (bool): Whether to ask for user confirmation before making POST, PUT, or DELETE requests, Default to True.
            debug (bool): set log level to DEBUG. Default INFO.
        """

        self.logger = logger
        self.providers = providers

        super().__init__(
            app=app,
            base_url=base_url,
            auth=auth,
            ignore_routes=ignore_routes,
            allow_routes=allow_routes,
            logger=self.logger,
        )

        self.model = model
        self.model_data = model_data
        self.agent_provider = agent_provider

        self.verify_api_call = kwargs.get("verify_api_call", True)

        self.assistant = self.get_ai_assistant(**kwargs)

    def add_app_description(self):
        existing_lifespan = self.app.router.lifespan_context

        @asynccontextmanager
        async def lifespan_handler(app: FastAPI):
            async with existing_lifespan(app):
                self.logger.info(
                    f"🚀 FastAPI Agent is Running on \033[1m{self.base_url}/agent/chat\033[0m"
                )
                yield

        self.app.router.lifespan_context = lifespan_handler

        # add FastAPI Agent included to app description
        desc = f'<br><b>🚀 FastAPI Agent included:</b> use <a href="{self.base_url}/agent/chat">{self.base_url}/agent/chat</a> to chat with the agent'
        self.app.description += desc

    def get_ai_assistant(self, **kwargs):
        assistant = AIAgent.create(
            self.model,
            model_data=self.model_data,
            prompt=self.get_system_prompt(),
            provider=self.agent_provider,
            logger=self.logger,
            **kwargs
        )

        @assistant.add_custom_tool
        async def api_request(
            ctx: RunContext[None],
            method: str,
            path: str,
            data: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
            params: Optional[Dict[str, str]] = None,
        ) -> APIResponse:
            """
            Make HTTP API requests to external services

            Args:
                method: HTTP method (GET, POST, PUT, DELETE)
                path: clean API endpoint path without query params (e.g., '/get', '/create')
                data: JSON data for POST/PUT requests
                headers: HTTP headers dictionary
                params: Query parameters for GET requests or additional params

            Returns:
                APIResponse: Structured response with status, data, and headers
            """
            # Prepare kwargs for execute_route
            kwargs = params.copy() if params else {}
            if data:
                kwargs["data"] = data

            if headers:
                kwargs["header"] = headers

            self.logger.debug(f"kwargs: {kwargs}")

            try:
                result = await self.execute_route(method, path, **kwargs)

                return APIResponse(
                    status_code=result.get("status_code", 0),
                    data=result.get("data", {}),
                    headers=result.get("headers", {}),
                    error=result.get("error"),
                )
            except Exception as e:
                return APIResponse(status_code=0, data={}, headers={}, error=str(e))

        return assistant

    def get_api_context_prompt(self) -> str:
        """Get system prompt for LLM with API context"""
        return (
            f"This is the API app info:\n"
            f"{self.get_openapi_spec()}\n"
            "----------------------------------------\n\n"
            "Those are the API Routes Available:\n"
            f"{self.get_routes_summary()}\n"
            f"This is the base url of the API: {self.base_url}\n"
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for LLM with API context"""

        return 'You are a helpful and concise assistant.'

    async def chat(self, user_input: str, bin_content: Optional[List[BinaryContent]] = None, history: Optional[list[str]] = None):
        if not history:
            history = []
        result, history, usage = await self.assistant.chat(message=user_input, bin_content=bin_content, history=history)
        return result, history, usage

    # def fix_cors(self):
    #     from fastapi.middleware.cors import CORSMiddleware

    #     allow_methods = self.get_allow_methods() + ["OPTIONS"]
    #     self.app.add_middleware(
    #         CORSMiddleware,
    #         # allow_origins=[self.base_url],
    #         # allow_credentials=True,
    #         allow_methods=list(set(allow_methods)),  # Make sure OPTIONS is included
    #         # allow_headers=["*"],
    #     )

    async def verify_dependencies(self, auth: str = Header(...)):
        self.logger.info("checking dependencies...")
        _depends = json.loads(auth)
        if _depends != self.depends:
            raise HTTPException(
                status_code=401, detail=f"Could not validate {_depends}"
            )
