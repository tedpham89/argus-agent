"""Aerondight local DB — stores synced scores and regime data from the private research system."""

import sqlite3
from pathlib import Path

AERONDIGHT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "aerondight.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(AERONDIGHT_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_aerondight_db():
    """Create tables if they don't exist."""
    AERONDIGHT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS analysis_scores (
            symbol VARCHAR(20) NOT NULL,
            date DATE NOT NULL,
            model_type VARCHAR(20) NOT NULL,
            fundamental_score FLOAT,
            valuation_score FLOAT,
            quality_score FLOAT,
            growth_score FLOAT,
            balance_sheet_score FLOAT,
            technical_score FLOAT,
            sector_score FLOAT,
            combined_score FLOAT,
            signal VARCHAR(10),
            trend_score FLOAT,
            updated_at DATETIME,
            PRIMARY KEY (symbol, date, model_type)
        );

        CREATE TABLE IF NOT EXISTS regime_states (
            date DATE PRIMARY KEY,
            hmm_regime INTEGER,
            hmm_regime_label VARCHAR(50),
            hmm_confidence FLOAT,
            xgb_regime INTEGER,
            xgb_confidence FLOAT,
            regime_agreement BOOLEAN,
            updated_at DATETIME
        );

        CREATE INDEX IF NOT EXISTS ix_aero_score_symbol ON analysis_scores (symbol);
        CREATE INDEX IF NOT EXISTS ix_aero_score_date ON analysis_scores (date);
    """)
    conn.close()


def db_exists() -> bool:
    return AERONDIGHT_DB_PATH.exists()
