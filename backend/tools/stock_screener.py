"""Stock screener tool — query top/bottom stocks by score and signal from Aerondight data."""

import json
from langchain_core.tools import tool

from backend.db.aerondight_db import db_exists, get_connection


@tool
def screen_stocks(signal: str = "", top_n: int = 10, sort: str = "desc") -> str:
    """Screen stocks by signal and score. Use this to find top-ranked or bottom-ranked stocks.
    Args: signal (optional, filter by BUY/SELL/WATCH), top_n (number of results, default 10),
    sort (desc for highest scores first, asc for lowest). Returns latest long_term scores."""
    if not db_exists():
        return json.dumps({
            "error": "No Aerondight data available. Stock screening requires synced research data.",
            "source": "none",
        }, indent=2)

    conn = get_connection()

    # Get the latest date available
    latest = conn.execute(
        "SELECT MAX(date) as d FROM analysis_scores WHERE model_type = 'long_term'"
    ).fetchone()
    if not latest or not latest["d"]:
        conn.close()
        return json.dumps({"error": "No scores in database", "source": "aerondight"}, indent=2)
    latest_date = latest["d"]

    order = "DESC" if sort.lower() == "desc" else "ASC"
    signal = signal.strip().upper()

    if signal:
        rows = conn.execute(
            f"""SELECT symbol, date, combined_score, fundamental_score, valuation_score,
                       quality_score, growth_score, technical_score, trend_score, signal
                FROM analysis_scores
                WHERE model_type = 'long_term' AND date = ? AND signal = ?
                ORDER BY combined_score {order}
                LIMIT ?""",
            (latest_date, signal, top_n),
        ).fetchall()
    else:
        rows = conn.execute(
            f"""SELECT symbol, date, combined_score, fundamental_score, valuation_score,
                       quality_score, growth_score, technical_score, trend_score, signal
                FROM analysis_scores
                WHERE model_type = 'long_term' AND date = ?
                ORDER BY combined_score {order}
                LIMIT ?""",
            (latest_date, top_n),
        ).fetchall()
    conn.close()

    results = []
    for r in rows:
        ticker = r["symbol"].replace(".US", "")
        results.append({
            "ticker": ticker,
            "combined_score": round(r["combined_score"] * 10, 1),
            "fundamental": round(r["fundamental_score"] * 10, 1),
            "valuation": round(r["valuation_score"] * 10, 1),
            "quality": round(r["quality_score"] * 10, 1),
            "growth": round(r["growth_score"] * 10, 1),
            "technical": round(r["technical_score"] * 10, 1),
            "trend": round(r["trend_score"] * 10, 1),
            "signal": r["signal"],
        })

    return json.dumps({
        "as_of": latest_date,
        "filter": signal or "ALL",
        "sort": sort,
        "count": len(results),
        "stocks": results,
        "source": "aerondight",
    }, indent=2)
