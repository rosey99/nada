import os
import re
import logging

import redis.asyncio as redis

from pydantic import BaseModel, ConfigDict, Field, ImportString, EmailStr
from pydantic_ai.common_tools.web_fetch import web_fetch_tool
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai_harness import Shell, FileSystem
from nada.agents.pydantic_ai import PydanticAIAgent

from nada.llm.common.provider import ProviderCollection
from nada.models import AgentQuery
#from nada.settings import providers

from typing import Any, Dict, List, Optional, Set, Annotated
from slugify import slugify
#from langchain.tools import tool, BaseTool
from pydantic import BaseModel, Field
#from pydantic_ai_harness.experimental.planning import Planning, PlanningToolset
from pydantic_ai.tools import AgentDepsT, RunContext, Tool
from pydantic_ai.toolsets import AbstractToolset
from pydantic_ai.capabilities import AbstractCapability



logger = logging.getLogger(__name__)


class PlanStep(BaseModel):

    job_id: str = Field(
        description="JobID assigned by dispatcher. Used for tracking results, identical for each step.",
    )
    agent_query: AgentQuery = Field(
        description="Instructions for this step, including prompt, and optionally model, provider, and message history."
    )
    # TODO langchain tool needs a pydantic schema, maybe use BaseTool?
    tool_names: Optional[List[str]] = Field(
        description="The names of agent tools required for execution of this step."
                    "Only use tool names that are available in your tool listing."
    )
    # parallel: bool = Field(
    #     description="Whether the step can be executed concurrently with adjacent PlanSteps. Only following steps "
    #                 "with parallel = True can be executed concurrently with this step, until parallel = False is encountered",
    #     default=False
    # )
    tags: Optional[Set[str]] | None = Field(
        description="Optional list of tags, used by router.",
        default_factory=set
    )
    # child_steps: Optional[List['PlanStep']] = Field(
    #     description="Additional PlanSteps that should execute following completion of this PlanStep."
    # )

# The result class that is created in all callbacks
class PlanStepResult(BaseModel):
    agent_response: Optional[str] | None = Field(description="The text response received from the agent")
    errors: List[str] | None = Field(description="A list of error messages", default_factory=list)


class Plan(BaseModel):

    steps: List[PlanStep] = Field(
        description="Sequential list of steps to be attempted in order."
                    "At least 1 step is required."
    )
    results: Optional[List[PlanStepResult]] = Field(
        description="List of results, may be empty.",
        default_factory=list
    )


class AgentCollection:
    def __init__(self, agent_provider_list: List[dict]):

        # TODO for now validate here in init
        self.agent_providers = {slugify(provider['name']): AgentProvider(**provider) for provider in agent_provider_list}


class AgentTooling(BaseModel):
    name: str
    tool_type: str  # helper for provider abstraction, could be 'capability', or 'tool' for pydantic AI
    get_tool: ImportString = Field(description="", default=None, exclude=True)
    default_args: Dict | None
    description: str


some_tools = {
    "duckduckgo": {
        'name': "duckduckgo",
        'tool_type': 'tool',
        'get_tool': 'pydantic_ai.common_tools.duckduckgo.duckduckgo_search_tool',
        'default_args': None,
        'description': "Search the web with DuckDuckGo"
    },
    "web_fetch":
    {
        'name': "web_fetch",
        'tool_type': 'tool',
        'get_tool': 'pydantic_ai.common_tools.web_fetch.web_fetch_tool',
        'default_args': {'max_content_length': None},
        'description': "Visit web pages with optional markdown conversion"
    },
    "shell":
    {
        'name': "shell",
        'tool_type': 'capability',
        'get_tool': 'pydantic_ai_harness.Shell',
        'default_args': None,
        'description': "Shell command executor"
    },
    "filesystem":
    {
        'name': "filesystem",
        'tool_type': 'capability',
        'get_tool': 'pydantic_ai_harness.FileSystem',
        'default_args': None,
        'description': "Access the local filesystem"
    },

}


class AgentCapabilities(BaseModel):
    args_capabilities: Dict[str, Dict[str, Any]] | None = Field(description="", default_factory=dict)
    capabilities: Dict[str, AgentTooling] | None = Field(description="", default_factory=dict)


class AgentModel(BaseModel):
    name: str | None = None
    description: str | None
    # optional override hook for get_agent func
    get_agent: ImportString | None = Field(description="", default=None, exclude=True)
    # also optional, as it may be set in get_agrnt
    system_prompt: str | None = None
    capabilities: AgentCapabilities


class AgentProvider(BaseModel):
    name: str
    agents: Dict[str, AgentModel]
    capabilities: AgentCapabilities | None
    get_agent: ImportString | None = Field(description="", default=None, exclude=True)
    args_agents: Dict[str, Dict[str, Any]] | None = Field(description="Agent override arguments", default_factory=dict)

fastapi_agent = {
    'name': 'nadaAgent',
    'description': 'Built-in default agent',
    'get_agent': None,
    'system_prompt': 'You are a helpful and concise AI agent.',
    'capabilities': {"capabilities": some_tools, "args_capabilities": {k: v['default_args'] for k,v in some_tools.items() if v['default_args'] is not None}}
}

agent_provider = {
    'name': 'pydantic_ai',
    'agents': {'fastapi_agent': fastapi_agent,},
    'capabilities': {"capabilities": some_tools, "args_capabilities": {k: v['default_args'] for k,v in some_tools.items() if v['default_args'] is not None}},
}

agent_providers = [agent_provider]


def get_planning_agent(model, system_prompt: str, tools: list | None = None, capabilities: list | None = None, request_settings: dict | None = None):
    """Create the planning or evaluator agent with system prompt and model"""
    logger.info(f"initialzing planning agent with {model if isinstance(model, str) else model.__class__}")
    tools = tools or []
    capabilities = capabilities or []
    return PydanticAIAgent(
        model=model,
        system_prompt=system_prompt,
        output_type=Plan,
        tools=tools,
        capabilities=capabilities,
        settings=request_settings,
    )
