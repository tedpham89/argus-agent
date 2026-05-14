"""Stock scorer tool — uses synced Aerondight data when available, falls back to mock."""

import json
from langchain_core.tools import tool

from backend.db.aerondight_db import db_exists, get_connection

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


def _query_real_score(ticker: str) -> dict | None:
    """Try to get real score from synced Aerondight DB."""
    if not db_exists():
        return None
    # Aerondight uses "TICKER.US" format
    symbol = f"{ticker}.US" if "." not in ticker else ticker
    conn = get_connection()
    row = conn.execute(
        """SELECT * FROM analysis_scores
           WHERE symbol = ? AND model_type = 'long_term'
           ORDER BY date DESC LIMIT 1""",
        (symbol,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


@tool
def score_stock(ticker: str) -> str:
    """Score a stock using a quantitative multi-factor model.
    Returns composite score (0-100), factor breakdown, and signal (BUY/HOLD/AVOID).
    Uses real Aerondight research scores when available."""
    ticker = ticker.strip().upper()

    real = _query_real_score(ticker)
    if real:
        # Scores in Aerondight are 0-10, scale to 0-100 for display
        return json.dumps({
            "ticker": ticker,
            "composite_score": round(real["combined_score"] * 10, 1),
            "factors": {
                "fundamental": round(real["fundamental_score"] * 10, 1),
                "valuation": round(real["valuation_score"] * 10, 1),
                "quality": round(real["quality_score"] * 10, 1),
                "growth": round(real["growth_score"] * 10, 1),
                "balance_sheet": round(real["balance_sheet_score"] * 10, 1),
                "technical": round(real["technical_score"] * 10, 1),
                "sector": round(real["sector_score"] * 10, 1),
                "trend": round(real["trend_score"] * 10, 1),
            },
            "signal": real["signal"],
            "confidence": "HIGH" if real["combined_score"] > 7.5 or real["combined_score"] < 4.0 else "MEDIUM",
            "as_of": real["date"],
            "model_type": real["model_type"],
            "source": "aerondight",
        }, indent=2)

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
