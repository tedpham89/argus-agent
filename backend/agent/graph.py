"""LangGraph state graph definition — the agent's brain."""

import uuid

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from backend.agent.state import AgentState
from backend.agent.nodes import (
    planner_node,
    executor_node,
    route_after_execute,
    validator_node,
    route_after_validate,
    response_node,
)

# Build the graph
graph_builder = StateGraph(AgentState)

# Add nodes
graph_builder.add_node("plan", planner_node)
graph_builder.add_node("execute", executor_node)
graph_builder.add_node("validate", validator_node)
graph_builder.add_node("respond", response_node)

# Add edges
graph_builder.add_edge(START, "plan")
graph_builder.add_edge("plan", "execute")
graph_builder.add_conditional_edges("execute", route_after_execute, {
    "execute": "execute",
    "validate": "validate",
})
graph_builder.add_conditional_edges("validate", route_after_validate, {
    "respond": "respond",
})
graph_builder.add_edge("respond", END)

# Compile with checkpointer for multi-user thread isolation
checkpointer = MemorySaver()
agent = graph_builder.compile(checkpointer=checkpointer)


async def run_agent(message: str, thread_id: str | None = None) -> dict:
    """Run the agent on a user message.

    Args:
        message: The user's natural language instruction
        thread_id: Optional thread ID for conversation continuity.
                   Generated automatically if not provided.

    Returns:
        dict with thread_id, plan (steps + results), final_response, and status
    """
    if thread_id is None:
        thread_id = str(uuid.uuid4())

    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "messages": [{"role": "user", "content": message}],
        "plan": [],
        "current_step": 0,
        "needs_approval": False,
        "final_response": None,
    }

    result = await agent.ainvoke(initial_state, config=config)

    return {
        "thread_id": thread_id,
        "plan": [step.model_dump() for step in result["plan"]],
        "final_response": result["final_response"],
        "status": "completed",
    }


async def resume_agent(thread_id: str, approved: bool) -> dict:
    """Resume agent after human approval.

    Placeholder for Phase 2 when we add interrupt() for confirmation gates.
    """
    return {
        "thread_id": thread_id,
        "status": "approved" if approved else "rejected",
        "message": "Approval flow will be implemented with LangGraph interrupt()",
    }
