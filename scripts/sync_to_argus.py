"""Sync Aerondight research data to Argus Agent.

Reads analysis_scores and regime_states from the local Aerondight DB
and POSTs them to the Argus /data/sync endpoint.

Usage:
    python scripts/sync_to_argus.py [--url URL] [--days N] [--dry-run]

Environment:
    SYNC_API_KEY  — required, must match the key configured on the Argus server
    ARGUS_URL     — optional, defaults to https://argus-agent.dev
"""

import argparse
import json
import sqlite3
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import httpx

DEFAULT_AERONDIGHT_DB = Path.home() / "Documents" / "ClaudeProject" / "equity-research - v2" / "data" / "equity_research.db"
DEFAULT_ARGUS_URL = "https://argus-agent.dev"
BATCH_SIZE = 500


def get_scores(conn: sqlite3.Connection, since_date: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT symbol, date, model_type, fundamental_score, valuation_score,
                  quality_score, growth_score, balance_sheet_score, technical_score,
                  sector_score, combined_score, signal, trend_score, updated_at
           FROM analysis_scores
           WHERE date >= ? AND model_type = 'long_term'
           ORDER BY date""",
        (since_date,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_regime(conn: sqlite3.Connection, since_date: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT date, hmm_regime, hmm_regime_label, hmm_confidence,
                  xgb_regime, xgb_confidence, regime_agreement, updated_at
           FROM regime_states
           WHERE date >= ?
           ORDER BY date""",
        (since_date,),
    ).fetchall()
    return [dict(r) for r in rows]


def sync(argus_url: str, api_key: str, scores: list[dict], regime: list[dict], dry_run: bool = False):
    url = f"{argus_url.rstrip('/')}/data/sync"

    if dry_run:
        print(f"[DRY RUN] Would POST to {url}")
        print(f"  Scores: {len(scores)} rows")
        print(f"  Regime: {len(regime)} rows")
        if scores:
            print(f"  Score date range: {scores[0]['date']} to {scores[-1]['date']}")
        if regime:
            print(f"  Regime date range: {regime[0]['date']} to {regime[-1]['date']}")
        return

    # Send regime in one shot (small table)
    # Send scores in batches
    total_scores = 0
    for i in range(0, max(len(scores), 1), BATCH_SIZE):
        batch = scores[i : i + BATCH_SIZE]
        payload = {
            "scores": batch if batch else None,
            "regime": regime if i == 0 else None,  # send regime only with first batch
        }
        resp = httpx.post(url, json=payload, headers={"X-API-Key": api_key}, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        total_scores += result["synced"]["scores"]
        if i == 0:
            print(f"  Regime synced: {result['synced']['regime']} rows")

    print(f"  Scores synced: {total_scores} rows")
    print("Sync complete.")


def main():
    parser = argparse.ArgumentParser(description="Sync Aerondight data to Argus Agent")
    parser.add_argument("--url", default=os.getenv("ARGUS_URL", DEFAULT_ARGUS_URL), help="Argus Agent URL")
    parser.add_argument("--db", default=str(DEFAULT_AERONDIGHT_DB), help="Path to Aerondight DB")
    parser.add_argument("--days", type=int, default=30, help="Sync data from last N days (default: 30)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be synced without sending")
    args = parser.parse_args()

    api_key = os.getenv("SYNC_API_KEY")
    if not api_key and not args.dry_run:
        print("Error: SYNC_API_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Error: Aerondight DB not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    since_date = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
    print(f"Reading from: {db_path}")
    print(f"Syncing to:   {args.url}")
    print(f"Since:        {since_date}")

    conn = sqlite3.connect(str(db_path))
    scores = get_scores(conn, since_date)
    regime = get_regime(conn, since_date)
    conn.close()

    print(f"Found {len(scores)} score rows, {len(regime)} regime rows")
    sync(args.url, api_key or "", scores, regime, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
