import os
import re

from typing import List, Optional

#from langchain.tools import tool, BaseTool
from pydantic import BaseModel, Field
from pydantic_ai_harness.experimental.planning import Planning, PlanItem, PlanningToolset

class PlanStep(BaseModel):

    index: int = Field(
        description="Numerical index of this PlanStep. Index begins at 1 and increments by 1 for each PlanStep. ",
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
        description="Whether the step can be executed concurrently with adjacent PlanSteps."
    )
    child_steps: Optional[List['PlanStep']] = Field(
        description="Additional PlanSteps that should execute following completion of this PlanStep."
    )

# TODO is this deprecated? No warnings
PlanStep.update_forward_refs()

class Plan(BaseModel):

    steps: List[PlanStep] = Field(
        description="Sequential list of steps to be attempted in order of PlanStep index."
                    "At least 1 step is required."
    )
