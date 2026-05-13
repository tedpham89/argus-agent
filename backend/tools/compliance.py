"""Compliance rules engine — retrieves rules via RAG, checks portfolio."""

import json
import sqlite3
from pathlib import Path

from langchain_core.tools import tool

try:
    import chromadb
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
except ImportError:
    chromadb = None

DB_PATH = Path(__file__).parent.parent / "data" / "portfolio.db"
CHROMA_PATH = Path(__file__).parent.parent / "data" / "chroma_data"
RULES_PATH = Path(__file__).parent.parent / "data" / "compliance_rules.json"

# Compliance rules to embed
COMPLIANCE_RULES = [
    {
        "id": "conc_single",
        "category": "concentration",
        "rule": "No single equity position may exceed 5% of total portfolio value",
        "severity": "HIGH",
        "check_field": "weight_pct",
        "threshold": 5.0,
    },
    {
        "id": "conc_sector",
        "category": "concentration",
        "rule": "Combined exposure to any single sector must not exceed 25% of total portfolio",
        "severity": "HIGH",
        "check_field": "sector_weight",
        "threshold": 25.0,
    },
    {
        "id": "credit_quality",
        "category": "credit",
        "rule": "All fixed income positions must maintain investment grade rating (BBB- or above)",
        "severity": "HIGH",
        "check_field": "rating",
        "threshold": "BBB-",
    },
    {
        "id": "cash_min",
        "category": "liquidity",
        "rule": "Cash and equivalents must represent at least 2% of total portfolio value",
        "severity": "MEDIUM",
        "check_field": "cash_weight",
        "threshold": 2.0,
    },
    {
        "id": "conc_top5",
        "category": "concentration",
        "rule": "Top 5 positions combined must not exceed 30% of total portfolio value",
        "severity": "MEDIUM",
        "check_field": "top5_weight",
        "threshold": 30.0,
    },
    {
        "id": "asset_diversification",
        "category": "diversification",
        "rule": "No single asset class may exceed 70% of total portfolio value",
        "severity": "MEDIUM",
        "check_field": "asset_class_weight",
        "threshold": 70.0,
    },
    {
        "id": "position_minimum",
        "category": "efficiency",
        "rule": "Individual positions should represent at least 0.5% of portfolio to be meaningful",
        "severity": "LOW",
        "check_field": "weight_pct",
        "threshold": 0.5,
    },
    {
        "id": "sector_minimum",
        "category": "diversification",
        "rule": "Portfolio should have exposure to at least 6 distinct sectors",
        "severity": "LOW",
        "check_field": "sector_count",
        "threshold": 6,
    },
]


def _get_chroma_collection():
    """Get or create the compliance rules collection."""
    if chromadb is None:
        return None

    client = chromadb.Client()  # in-memory for simplicity
    ef = DefaultEmbeddingFunction()

    collection = client.get_or_create_collection(
        name="compliance_rules",
        embedding_function=ef,
    )

    # Seed if empty
    if collection.count() == 0:
        collection.add(
            documents=[r["rule"] for r in COMPLIANCE_RULES],
            ids=[r["id"] for r in COMPLIANCE_RULES],
            metadatas=[{
                "category": r["category"],
                "severity": r["severity"],
            } for r in COMPLIANCE_RULES],
        )

    return collection


def _get_holdings_data() -> list[dict]:
    """Get all holdings from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM holdings ORDER BY weight_pct DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _run_compliance_checks(check_type: str) -> list[dict]:
    """Run compliance checks against actual portfolio data."""
    holdings = _get_holdings_data()
    violations = []

    if not holdings:
        return [{"error": "No holdings data found"}]

    # Single position concentration
    if check_type in ("concentration", "all"):
        for h in holdings:
            if h["weight_pct"] > 5.0:
                violations.append({
                    "rule": "Single position limit (5%)",
                    "severity": "HIGH",
                    "violator": h["ticker"],
                    "current_value": f"{h['weight_pct']}%",
                    "limit": "5%",
                    "recommendation": f"Reduce {h['ticker']} by {round(h['weight_pct'] - 5.0, 2)}pp",
                })

    # Sector concentration
    if check_type in ("concentration", "all"):
        sector_weights = {}
        for h in holdings:
            sector_weights[h["sector"]] = sector_weights.get(h["sector"], 0) + h["weight_pct"]
        for sector, weight in sector_weights.items():
            if weight > 25.0:
                violations.append({
                    "rule": "Sector limit (25%)",
                    "severity": "HIGH",
                    "violator": sector,
                    "current_value": f"{round(weight, 2)}%",
                    "limit": "25%",
                    "recommendation": f"Reduce {sector} exposure by {round(weight - 25.0, 2)}pp",
                })

    # Top 5 concentration
    if check_type in ("concentration", "all"):
        top5_weight = sum(h["weight_pct"] for h in holdings[:5])
        if top5_weight > 30.0:
            top5_names = ", ".join(h["ticker"] for h in holdings[:5])
            violations.append({
                "rule": "Top 5 concentration limit (30%)",
                "severity": "MEDIUM",
                "violator": top5_names,
                "current_value": f"{round(top5_weight, 2)}%",
                "limit": "30%",
                "recommendation": "Redistribute weight from top positions",
            })

    # Cash minimum
    if check_type in ("liquidity", "all"):
        cash_weight = sum(h["weight_pct"] for h in holdings if h["asset_class"] == "cash")
        if cash_weight < 2.0:
            violations.append({
                "rule": "Cash minimum (2%)",
                "severity": "MEDIUM",
                "violator": "Cash allocation",
                "current_value": f"{round(cash_weight, 2)}%",
                "limit": "2% minimum",
                "recommendation": f"Increase cash by {round(2.0 - cash_weight, 2)}pp",
            })

    # Credit quality
    if check_type in ("credit", "all"):
        sub_ig_ratings = {"BB+", "BB", "BB-", "B+", "B", "B-", "CCC", "CC", "C", "D"}
        for h in holdings:
            if h.get("rating") and h["rating"] in sub_ig_ratings:
                violations.append({
                    "rule": "Investment grade minimum (BBB-)",
                    "severity": "HIGH",
                    "violator": h["ticker"],
                    "current_value": h["rating"],
                    "limit": "BBB- minimum",
                    "recommendation": f"Review {h['ticker']} for potential exit",
                })

    # Sector count
    if check_type in ("diversification", "all"):
        sector_count = len(set(h["sector"] for h in holdings))
        if sector_count < 6:
            violations.append({
                "rule": "Sector diversification (min 6 sectors)",
                "severity": "LOW",
                "violator": "Portfolio",
                "current_value": f"{sector_count} sectors",
                "limit": "6 minimum",
                "recommendation": "Add exposure to underrepresented sectors",
            })

    if not violations:
        return [{"status": "PASS", "message": f"No violations found for {check_type} checks"}]

    return violations


@tool
def check_compliance(check_type: str = "all") -> str:
    """Check portfolio against compliance and risk rules.
    check_type options: concentration, credit, liquidity, diversification, all.
    Returns violations with severity, details, and recommendations."""

    # RAG: retrieve relevant rules for context
    collection = _get_chroma_collection()
    retrieved_rules = []
    if collection:
        results = collection.query(
            query_texts=[check_type],
            n_results=5,
        )
        retrieved_rules = results.get("documents", [[]])[0]

    # Run actual checks
    violations = _run_compliance_checks(check_type)

    return json.dumps({
        "check_type": check_type,
        "rules_evaluated": retrieved_rules,
        "violations": violations,
        "total_violations": len([v for v in violations if "status" not in v]),
    }, indent=2)
