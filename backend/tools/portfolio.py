"""Portfolio holdings tool — queries the SQLite portfolio database."""

import json
import sqlite3
from pathlib import Path

from langchain_core.tools import tool

DB_PATH = Path(__file__).parent.parent / "data" / "portfolio.db"


def _query(sql: str, params: tuple = ()) -> list[dict]:
    """Run a SQL query and return results as list of dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@tool
def query_holdings(sector: str = "", asset_class: str = "") -> str:
    """Query portfolio holdings. Optionally filter by sector or asset_class.
    Returns all positions if no filters provided."""
    conditions = []
    params = []
    if sector:
        conditions.append("sector = ?")
        params.append(sector)
    if asset_class:
        conditions.append("asset_class = ?")
        params.append(asset_class)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT * FROM holdings {where} ORDER BY weight_pct DESC"
    results = _query(sql, tuple(params))
    return json.dumps(results, indent=2)


@tool
def get_sector_breakdown() -> str:
    """Get portfolio sector breakdown with total weight and position count per sector."""
    sql = """
        SELECT sector,
               COUNT(*) as position_count,
               ROUND(SUM(weight_pct), 2) as total_weight,
               ROUND(SUM(market_value), 2) as total_value
        FROM holdings
        GROUP BY sector
        ORDER BY total_weight DESC
    """
    results = _query(sql)
    return json.dumps(results, indent=2)


@tool
def get_top_positions(n: int = 10) -> str:
    """Get the top N positions by portfolio weight."""
    sql = "SELECT * FROM holdings ORDER BY weight_pct DESC LIMIT ?"
    results = _query(sql, (n,))
    return json.dumps(results, indent=2)
