import os
import re

from typing import List, Optional

#from langchain.tools import tool, BaseTool
from pydantic import BaseModel, Field
#from pydantic_ai_harness.experimental.planning import Planning, PlanningToolset

class PlanStep(BaseModel):

    job_id: str = Field(
        description="JobID assigned by dispatcher. Used for aggregating results, identical for each step.",
        gt=0
    )
    prompt: str = Field(
        description="Instructions for this step, passed directly to the executing agent."
    )
    # TODO langchain tool needs a pydantic schema, maybe use BaseTool?
    tool_names: Optional[List[str]] = Field(
        description="The names of agent tools required for execution of this step."
                    "Only use tool names that are available in your tool listing."
    )
    parallel: bool = Field(
        description="Whether the step can be executed concurrently with adjacent PlanSteps. Only following steps "
                    "with parallel = True will be executed concurrently with this step, until parallel = False is encountered",
        default=False
    )
    tags: Optional[List[str]] | None = Field(
        description="Optional list of tags, used by router.",
        default=None
    )
    # child_steps: Optional[List['PlanStep']] = Field(
    #     description="Additional PlanSteps that should execute following completion of this PlanStep."
    # )

# TODO is this deprecated? No warnings
#PlanStep.update_forward_refs()
class PlanStepResult(BaseModel):
    pass


class Plan(BaseModel):

    steps: List[PlanStep] = Field(
        description="Sequential list of steps to be attempted in order."
                    "At least 1 step is required."
    )
    results: Optional[List[PlanStepResult]] = Field(
        description="List of results, may be empty.",
        default_factory=list
    )
