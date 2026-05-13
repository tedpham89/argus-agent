"""Stock scorer tool — mock implementation for public repo.

In production, this calls the private Aerondight API.
Set AERONDIGHT_API_URL and AERONDIGHT_API_KEY env vars to use real scores.
"""

import json
import os
from langchain_core.tools import tool

# Mock scores for demo purposes
MOCK_SCORES = {
    "NVDA": {"composite": 82, "momentum": 90, "value": 45, "quality": 88, "growth": 95, "signal": "BUY"},
    "AAPL": {"composite": 71, "momentum": 65, "value": 55, "quality": 92, "growth": 60, "signal": "HOLD"},
    "MSFT": {"composite": 75, "momentum": 70, "value": 60, "quality": 95, "growth": 72, "signal": "BUY"},
    "GOOGL": {"composite": 68, "momentum": 55, "value": 70, "quality": 85, "growth": 58, "signal": "HOLD"},
    "AMZN": {"composite": 77, "momentum": 75, "value": 40, "quality": 80, "growth": 90, "signal": "BUY"},
    "META": {"composite": 73, "momentum": 72, "value": 65, "quality": 78, "growth": 75, "signal": "HOLD"},
    "TSLA": {"composite": 55, "momentum": 60, "value": 20, "quality": 50, "growth": 85, "signal": "AVOID"},
    "JPM": {"composite": 70, "momentum": 62, "value": 75, "quality": 88, "growth": 45, "signal": "HOLD"},
    "JNJ": {"composite": 58, "momentum": 35, "value": 72, "quality": 90, "growth": 30, "signal": "HOLD"},
    "XOM": {"composite": 64, "momentum": 50, "value": 80, "quality": 70, "growth": 40, "signal": "HOLD"},
}


@tool
def score_stock(ticker: str) -> str:
    """Score a stock using a quantitative multi-factor model.
    Returns composite score (0-100), factor breakdown
    (momentum, value, quality, growth), and signal (BUY/HOLD/AVOID)."""
    ticker = ticker.strip().upper()

    # Check if private API is configured
    api_url = os.getenv("AERONDIGHT_API_URL")
    api_key = os.getenv("AERONDIGHT_API_KEY")

    if api_url and api_key:
        # TODO: Call real Aerondight API
        # response = httpx.get(f"{api_url}/score/{ticker}", headers={"Authorization": f"Bearer {api_key}"})
        pass

    # Fall back to mock scores
    if ticker in MOCK_SCORES:
        score = MOCK_SCORES[ticker]
        return json.dumps({
            "ticker": ticker,
            "composite_score": score["composite"],
            "factors": {
                "momentum": score["momentum"],
                "value": score["value"],
                "quality": score["quality"],
                "growth": score["growth"],
            },
            "signal": score["signal"],
            "confidence": "HIGH" if score["composite"] > 75 or score["composite"] < 40 else "MEDIUM",
            "source": "mock",
        }, indent=2)

    return json.dumps({
        "ticker": ticker,
        "composite_score": 50,
        "factors": {"momentum": 50, "value": 50, "quality": 50, "growth": 50},
        "signal": "HOLD",
        "confidence": "LOW",
        "source": "mock_default",
        "note": "No model data available for this ticker — returning neutral score",
    }, indent=2)
