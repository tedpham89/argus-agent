"""Market regime classifier — uses synced Aerondight data when available, falls back to mock."""

import json
from datetime import datetime

from langchain_core.tools import tool

from backend.db.aerondight_db import db_exists, get_connection

REGIME_GUIDANCE = {
    "bull_tech": "Bull regime led by tech/growth. Favor quality growth and momentum factors. Full allocation appropriate.",
    "bull_broad": "Broad bull market with wide participation. Favor equal-weight and value factors. Full allocation appropriate.",
    "correction": "Market correction underway. Reduce position sizes by 30-50%. Favor defensive sectors and quality factor.",
    "crisis": "Crisis regime — risk-off. Minimize equity exposure. Favor cash, treasuries, and inverse correlation assets.",
}


def _query_real_regime() -> dict | None:
    """Try to get real regime from synced Aerondight DB."""
    if not db_exists():
        return None
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM regime_states ORDER BY date DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


@tool
def get_market_regime() -> str:
    """Get current market regime classification.
    Returns regime label, confidence, and positioning guidance.
    Uses real Aerondight regime model when available."""

    real = _query_real_regime()
    if real:
        label = real["hmm_regime_label"] or "unknown"
        return json.dumps({
            "regime": label,
            "regime_id": real["hmm_regime"],
            "xgb_regime_id": real["xgb_regime"],
            "xgb_confidence": round(real["xgb_confidence"], 4) if real["xgb_confidence"] else None,
            "regime_agreement": bool(real["regime_agreement"]),
            "positioning_guidance": REGIME_GUIDANCE.get(label, "No specific guidance for this regime."),
            "as_of": real["date"],
            "source": "aerondight",
        }, indent=2)

    # Mock regime data
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
