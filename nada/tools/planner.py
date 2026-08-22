import os
import re
import logging

import redis.asyncio as redis

from pydantic import BaseModel, ConfigDict, Field, ImportString, EmailStr
from pydantic_ai.common_tools.web_fetch import web_fetch_tool
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai_harness import Shell, FileSystem
from pydantic_ai import Agent

from nada.llm.common.provider import ProviderCollection
from nada.models import AgentQuery
from nada.settings import providers

from typing import Dict, List, Optional, Set

#from langchain.tools import tool, BaseTool
from pydantic import Annotated, BaseModel, Field
#from pydantic_ai_harness.experimental.planning import Planning, PlanningToolset
from pydantic_ai.tools import AgentDepsT, RunContext, Tool
from pydantic_ai.toolsets import AbstractToolset
from pydantic_ai.capabilities import AbstractCapability
from .native_or_local import NativeOrLocalTool


logger = logging.getLogger(__name__)


class PlanStep(BaseModel):

    job_id: str = Field(
        description="JobID assigned by dispatcher. Used for tracking results, identical for each step.",
        gt=0
    )
    agent_query: AgentQuery = Field(
        description="Instructions for this step, including prompt, and optionally model, provider, and message history."
    )
    # TODO langchain tool needs a pydantic schema, maybe use BaseTool?
    tool_names: Optional[List[str]] = Field(
        description="The names of agent tools required for execution of this step."
                    "Only use tool names that are available in your tool listing."
    )
    parallel: bool = Field(
        description="Whether the step can be executed concurrently with adjacent PlanSteps. Only following steps "
                    "with parallel = True can be executed concurrently with this step, until parallel = False is encountered",
        default=False
    )
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
    success_flag: bool = Field(description="A value greater than 0 indicates success", default=False)


class Plan(BaseModel):

    steps: List[PlanStep] = Field(
        description="Sequential list of steps to be attempted in order."
                    "At least 1 step is required."
    )
    results: Optional[List[PlanStepResult]] = Field(
        description="List of results, may be empty.",
        default_factory=list
    )

class AgentCapabilities(BaseModel):
    _tools = {
        "duckduckgo": duckduckgo_search_tool,
        "web_fetch": web_fetch_tool
    }
    tools_args: Dict = {"web_fetch": {"max_content_length": None}}
    tools: Dict[str, NativeOrLocalTool[AgentDepsT]]
    capabilities: Dict[str, AbstractCapability[AgentDepsT]]


def get_planning_agent(model, system_prompt: str, tools: list | None = None, capabilities: list | None = None, request_settings: dict | None = None):
    """Create the planning or evaluator agent with system prompt and model"""
    logger.info(f"initialzing planning agent with {model if isinstance(model, str) else model.__class__}")
    tools = tools or []
    capabilities = capabilities or []
    return Agent(
        model=model,
        system_prompt=system_prompt,
        output_type=str,
        tools=tools,
        capabilities=capabilities,
        settings=request_settings,
    )
