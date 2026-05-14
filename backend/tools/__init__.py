"""Tool registry — central place for tool discovery and routing."""

from backend.tools.portfolio import (
    query_holdings,
    get_sector_breakdown,
    get_top_positions,
)
from backend.tools.market_data import get_market_data
from backend.tools.compliance import check_compliance
from backend.tools.stock_scorer import score_stock
from backend.tools.regime import get_market_regime
from backend.tools.historical_scores import query_historical_scores
from backend.tools.stock_screener import screen_stocks

# All tools the agent can call
TOOLS = [
    query_holdings,
    get_sector_breakdown,
    get_top_positions,
    get_market_data,
    check_compliance,
    score_stock,
    get_market_regime,
    query_historical_scores,
    screen_stocks,
]

_TOOL_MAP = {tool.name: tool for tool in TOOLS}


def get_tool_descriptions() -> str:
    """Return formatted descriptions of all tools for the planner prompt."""
    lines = []
    for tool in TOOLS:
        schema = tool.args_schema.model_json_schema() if tool.args_schema else {}
        props = schema.get("properties", {})
        args_desc = ", ".join(
            f"{k}: {v.get('type', 'any')}" for k, v in props.items()
        )
        lines.append(f"- {tool.name}({args_desc}): {tool.description}")
    return "\n".join(lines)


def get_tool_by_name(name: str):
    """Look up a tool by name. Returns None if not found."""
    return _TOOL_MAP.get(name)
