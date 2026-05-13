"""Market regime classifier — mock implementation for public repo.

In production, this calls the private Aerondight API for real regime state
derived from breadth, momentum, and sector rotation signals.
"""

import json
import os
from datetime import datetime

from langchain_core.tools import tool


@tool
def get_market_regime() -> str:
    """Get current market regime classification.
    Returns regime label (RISK_ON/RISK_OFF/TRANSITIONAL/CRISIS),
    confidence, supporting indicators, and positioning guidance."""

    # Check if private API is configured
    api_url = os.getenv("AERONDIGHT_API_URL")
    api_key = os.getenv("AERONDIGHT_API_KEY")

    if api_url and api_key:
        # TODO: Call real Aerondight API
        # response = httpx.get(f"{api_url}/regime", headers={"Authorization": f"Bearer {api_key}"})
        pass

    # Mock regime data — realistic snapshot
    return json.dumps({
        "regime": "TRANSITIONAL",
        "confidence": 0.65,
        "previous_regime": "RISK_ON",
        "regime_duration_days": 12,
        "indicators": {
            "market_breadth": {
                "advance_decline_ratio": 0.85,
                "pct_above_200dma": 52.3,
                "signal": "WEAKENING",
            },
            "momentum": {
                "spy_vs_200dma": "ABOVE",
                "rsp_vs_spy_trend": "DECLINING",
                "signal": "MIXED",
            },
            "volatility": {
                "vix_level": 18.5,
                "vix_trend": "RISING",
                "signal": "CAUTIOUS",
            },
            "sector_rotation": {
                "leadership": ["Technology", "Communication Services"],
                "lagging": ["Utilities", "Real Estate"],
                "rotation_stage": "LATE_CYCLE",
                "signal": "NARROWING",
            },
        },
        "positioning_guidance": (
            "Transitional regime with weakening breadth. "
            "Favor quality factor over momentum. "
            "Consider reducing position sizes by 20-30% vs full allocation. "
            "Maintain defensive sector hedges."
        ),
        "as_of": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": "mock",
    }, indent=2)
