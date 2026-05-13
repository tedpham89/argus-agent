"""LangGraph node functions for the agent."""

import json
import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from backend.agent.state import AgentState, PlanStep
from backend.agent.prompts import PLANNER_PROMPT, VALIDATOR_PROMPT, RESPONSE_PROMPT
from backend.tools import get_tool_descriptions, get_tool_by_name

logger = logging.getLogger(__name__)


def _get_llm():
    """Lazy-init the LLM so that env vars from .env are loaded first."""
    return ChatAnthropic(model="claude-sonnet-4-20250514", max_tokens=4096)


async def planner_node(state: AgentState) -> dict:
    """Decompose the user's request into a structured plan."""
    user_message = state["messages"][-1].content
    tool_descriptions = get_tool_descriptions()

    prompt = PLANNER_PROMPT.format(tool_descriptions=tool_descriptions)

    response = await _get_llm().ainvoke([
        SystemMessage(content=prompt),
        HumanMessage(content=user_message),
    ])

    try:
        steps_raw = json.loads(response.content)
        steps = [PlanStep(**s) for s in steps_raw]
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Planner failed to parse: {e}")
        steps = [PlanStep(
            step_number=1,
            description="Direct response — could not decompose into tool calls",
            tool_name="none",
            tool_args={},
        )]

    return {"plan": steps, "current_step": 0}


async def executor_node(state: AgentState) -> dict:
    """Execute the current step in the plan by calling the appropriate tool."""
    plan = state["plan"]
    idx = state["current_step"]

    if idx >= len(plan):
        return {"current_step": idx}

    step = plan[idx]
    step.status = "running"

    tool = get_tool_by_name(step.tool_name)
    if tool is None:
        step.status = "failed"
        step.result = f"Unknown tool: {step.tool_name}"
    else:
        try:
            result = tool.invoke(step.tool_args)
            step.result = str(result)
            step.status = "completed"
        except Exception as e:
            step.status = "failed"
            step.result = f"Error: {str(e)}"
            logger.error(f"Tool {step.tool_name} failed: {e}")

    plan[idx] = step
    return {"plan": plan, "current_step": idx + 1}


def route_after_execute(state: AgentState) -> str:
    """Decide whether to continue executing or validate."""
    idx = state["current_step"]
    plan = state["plan"]

    if idx < len(plan):
        return "execute"  # more steps to run
    return "validate"  # all steps done


async def validator_node(state: AgentState) -> dict:
    """Check if the plan results are complete and consistent."""
    user_message = state["messages"][-1].content

    plan_results = "\n".join(
        f"Step {s.step_number}: {s.description}\n"
        f"  Tool: {s.tool_name} | Status: {s.status}\n"
        f"  Result: {s.result}\n"
        for s in state["plan"]
    )

    prompt = VALIDATOR_PROMPT.format(
        user_message=user_message,
        plan_results=plan_results,
    )

    response = await _get_llm().ainvoke([
        SystemMessage(content=prompt),
        HumanMessage(content="Evaluate the plan results above."),
    ])

    try:
        validation = json.loads(response.content)
        if validation.get("status") == "incomplete":
            logger.warning(f"Validation issues: {validation.get('issues')}")
    except json.JSONDecodeError:
        pass

    return {"needs_approval": False}


def route_after_validate(state: AgentState) -> str:
    """Route to response generation."""
    # Future: could route to replan if validation fails
    return "respond"


async def response_node(state: AgentState) -> dict:
    """Synthesize tool results into a final user-facing response."""
    user_message = state["messages"][-1].content

    plan_results = "\n".join(
        f"Step {s.step_number}: {s.description}\n"
        f"  Result: {s.result}\n"
        for s in state["plan"]
        if s.status == "completed"
    )

    prompt = RESPONSE_PROMPT.format(
        user_message=user_message,
        plan_results=plan_results,
    )

    response = await _get_llm().ainvoke([
        SystemMessage(content=prompt),
        HumanMessage(content="Synthesize the results into a response."),
    ])

    return {"final_response": response.content}
