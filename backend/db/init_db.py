"""Initialize SQLite database with seed portfolio data."""

import json
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "portfolio.db"
SEED_PATH = DATA_DIR / "seed_holdings.json"


def init_database():
    """Create tables and seed data if database doesn't exist."""
    db_exists = DB_PATH.exists()

    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS holdings (
            ticker TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            sector TEXT NOT NULL,
            asset_class TEXT NOT NULL,
            shares REAL NOT NULL,
            price REAL NOT NULL,
            market_value REAL NOT NULL,
            weight_pct REAL NOT NULL,
            entry_date TEXT NOT NULL,
            rating TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            action TEXT NOT NULL,
            shares REAL NOT NULL,
            price REAL NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (ticker) REFERENCES holdings(ticker)
        )
    """)

    # Seed if empty
    count = conn.execute("SELECT COUNT(*) FROM holdings").fetchone()[0]
    if count == 0:
        with open(SEED_PATH) as f:
            holdings = json.load(f)

        conn.executemany(
            """INSERT INTO holdings
               (ticker, name, sector, asset_class, shares, price, market_value, weight_pct, entry_date, rating)
               VALUES (:ticker, :name, :sector, :asset_class, :shares, :price, :market_value, :weight_pct, :entry_date, :rating)""",
            holdings,
        )
        logger.info(f"Seeded {len(holdings)} positions into portfolio database")

    conn.commit()
    conn.close()
    logger.info(f"Database ready at {DB_PATH}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database()
