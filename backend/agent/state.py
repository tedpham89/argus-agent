"""Agent state schema for LangGraph."""

from typing import Annotated, Any
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages
from pydantic import BaseModel


class PlanStep(BaseModel):
    """A single step in the agent's plan."""
    step_number: int
    description: str
    tool_name: str
    tool_args: dict[str, Any]
    status: str = "pending"  # pending | running | completed | failed
    result: str | None = None


class AgentState(TypedDict):
    """Full state passed through the LangGraph graph."""
    messages: Annotated[list, add_messages]
    plan: list[PlanStep]
    current_step: int
    needs_approval: bool
    final_response: str | None
