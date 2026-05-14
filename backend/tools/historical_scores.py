"""Historical scores tool — query Aerondight score history over date ranges."""

import json
from langchain_core.tools import tool

from backend.db.aerondight_db import db_exists, get_connection


@tool
def query_historical_scores(ticker: str, start_date: str, end_date: str, model_type: str = "long_term") -> str:
    """Query historical stock scores over a date range.
    Args: ticker (e.g. AAPL), start_date (YYYY-MM-DD), end_date (YYYY-MM-DD),
    model_type (long_term or swing). Returns score history with signals."""
    ticker = ticker.strip().upper()

    if not db_exists():
        return json.dumps({
            "ticker": ticker,
            "error": "No Aerondight data available. Historical scores require synced research data.",
            "source": "none",
        }, indent=2)

    symbol = f"{ticker}.US" if "." not in ticker else ticker
    conn = get_connection()
    rows = conn.execute(
        """SELECT date, combined_score, fundamental_score, valuation_score,
                  quality_score, growth_score, technical_score, trend_score,
                  signal
           FROM analysis_scores
           WHERE symbol = ? AND model_type = ? AND date BETWEEN ? AND ?
           ORDER BY date""",
        (symbol, model_type, start_date, end_date),
    ).fetchall()
    conn.close()

    if not rows:
        return json.dumps({
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "model_type": model_type,
            "records": 0,
            "note": "No scores found for this ticker/date range.",
            "source": "aerondight",
        }, indent=2)

    history = []
    for r in rows:
        history.append({
            "date": r["date"],
            "combined_score": round(r["combined_score"] * 10, 1),
            "fundamental": round(r["fundamental_score"] * 10, 1),
            "valuation": round(r["valuation_score"] * 10, 1),
            "quality": round(r["quality_score"] * 10, 1),
            "growth": round(r["growth_score"] * 10, 1),
            "technical": round(r["technical_score"] * 10, 1),
            "trend": round(r["trend_score"] * 10, 1),
            "signal": r["signal"],
        })

    scores = [h["combined_score"] for h in history]
    return json.dumps({
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
        "model_type": model_type,
        "records": len(history),
        "summary": {
            "latest_score": scores[-1],
            "avg_score": round(sum(scores) / len(scores), 1),
            "min_score": min(scores),
            "max_score": max(scores),
            "latest_signal": history[-1]["signal"],
        },
        "history": history,
        "source": "aerondight",
    }, indent=2)
