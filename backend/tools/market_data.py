"""Market data tool — wraps yfinance for price and return data."""

import json
from datetime import datetime

from langchain_core.tools import tool

try:
    import yfinance as yf
except ImportError:
    yf = None


@tool
def get_market_data(tickers: str, period: str = "1mo") -> str:
    """Get current market data for one or more tickers (comma-separated).
    Returns current price, period return, 52-week high/low, and volume.
    Period options: 1d, 5d, 1mo, 3mo, 6mo, 1y, ytd."""
    if yf is None:
        return json.dumps({"error": "yfinance not installed"})

    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    results = []

    for symbol in ticker_list:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)

            if hist.empty:
                results.append({"ticker": symbol, "error": "No data found"})
                continue

            current_price = round(hist["Close"].iloc[-1], 2)
            start_price = round(hist["Close"].iloc[0], 2)
            period_return = round((current_price - start_price) / start_price * 100, 2)

            info = ticker.info
            results.append({
                "ticker": symbol,
                "current_price": current_price,
                "period_return_pct": period_return,
                "period": period,
                "high_52w": info.get("fiftyTwoWeekHigh"),
                "low_52w": info.get("fiftyTwoWeekLow"),
                "avg_volume": info.get("averageVolume"),
                "market_cap": info.get("marketCap"),
                "as_of": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
        except Exception as e:
            results.append({"ticker": symbol, "error": str(e)})

    return json.dumps(results, indent=2)
