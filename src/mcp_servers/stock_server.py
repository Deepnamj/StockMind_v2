import json
from datetime import datetime, timedelta, timezone

import yfinance as yf
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("StockMind Stock Data")

def safe_json(data):
    return json.dumps(data, default=str, ensure_ascii=False)

@mcp.tool()
def search_companies(query: str) -> str:
    """Search for publicly traded companies by name or ticker symbol."""
    try:
        result = yf.Search(query, max_results=8)
        quotes = []
        for item in result.quotes:
            quotes.append({
                "symbol": item.get("symbol"),
                "name": item.get("shortname") or item.get("longname"),
                "exchange": item.get("exchange"),
                "quote_type": item.get("quoteType"),
            })
        return safe_json({"query": query, "matches": quotes})
    except Exception as error:
        return safe_json({"error": f"Company search failed: {error}"})

@mcp.tool()
def get_stock_price(symbol: str) -> str:
    """Get the latest available quote and previous close for a ticker symbol."""
    try:
        ticker = yf.Ticker(symbol.upper())
        history = ticker.history(period="5d", interval="1d")
        if history.empty:
            return safe_json({"symbol": symbol.upper(), "error": "No price data found."})

        latest = history.iloc[-1]
        previous_close = float(history.iloc[-2]["Close"]) if len(history) > 1 else None
        current_price = float(latest["Close"])
        change = current_price - previous_close if previous_close is not None else None
        percent = (change / previous_close * 100) if previous_close else None

        return safe_json({
            "symbol": symbol.upper(),
            "price": current_price,
            "previous_close": previous_close,
            "change": change,
            "change_percent": percent,
            "currency": ticker.fast_info.get("currency"),
            "data_date": str(history.index[-1]),
            "source": "Yahoo Finance via yfinance",
            "note": "May be delayed; not guaranteed real-time."
        })
    except Exception as error:
        return safe_json({"symbol": symbol.upper(), "error": f"Price lookup failed: {error}"})

@mcp.tool()
def get_company_profile(symbol: str) -> str:
    """Get a company's business description, sector, industry, website and headquarters."""
    try:
        info = yf.Ticker(symbol.upper()).get_info()
        fields = [
            "symbol", "longName", "shortName", "longBusinessSummary", "sector",
            "industry", "website", "country", "city", "state", "fullTimeEmployees",
            "chiefExecutiveOfficer"
        ]
        profile = {}
        for field in fields:
            value = info.get(field)
            if value is not None:
                profile[field] = value
        if not profile:
            return safe_json({"symbol": symbol.upper(), "error": "Company profile unavailable."})
        return safe_json(profile)
    except Exception as error:
        return safe_json({"symbol": symbol.upper(), "error": f"Profile lookup failed: {error}"})

@mcp.tool()
def get_company_fundamentals(symbol: str) -> str:
    """Get selected company financial metrics such as market cap, P/E, EPS and revenue."""
    try:
        info = yf.Ticker(symbol.upper()).get_info()
        fields = [
            "marketCap", "trailingPE", "forwardPE", "trailingEps", "forwardEps",
            "totalRevenue", "revenueGrowth", "grossMargins", "operatingMargins",
            "profitMargins", "returnOnEquity", "debtToEquity", "dividendYield",
            "currency", "financialCurrency"
        ]
        metrics = {"symbol": symbol.upper()}
        for field in fields:
            value = info.get(field)
            if value is not None:
                metrics[field] = value
        if len(metrics) == 1:
            metrics["error"] = "Fundamental metrics unavailable."
        metrics["source"] = "Yahoo Finance via yfinance"
        return safe_json(metrics)
    except Exception as error:
        return safe_json({"symbol": symbol.upper(), "error": f"Fundamentals lookup failed: {error}"})

@mcp.tool()
def get_stock_history(symbol: str, period: str = "6mo", interval: str = "1d") -> str:
    """Get historical OHLCV data. Supported periods include 1mo, 3mo, 6mo, 1y, 2y and 5y."""
    allowed_periods = ["1mo", "3mo", "6mo", "1y", "2y", "5y"]
    allowed_intervals = ["1d", "1wk", "1mo"]
    if period not in allowed_periods or interval not in allowed_intervals:
        return safe_json({"error": "Unsupported period or interval."})
    try:
        history = yf.Ticker(symbol.upper()).history(period=period, interval=interval)
        if history.empty:
            return safe_json({"symbol": symbol.upper(), "error": "Historical data unavailable."})
        rows = []
        for date, row in history.tail(250).iterrows():
            rows.append({
                "date": str(date),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]),
            })
        return safe_json({
            "symbol": symbol.upper(), "period": period, "interval": interval,
            "prices": rows, "source": "Yahoo Finance via yfinance"
        })
    except Exception as error:
        return safe_json({"symbol": symbol.upper(), "error": f"History lookup failed: {error}"})

@mcp.tool()
def get_stock_news(symbol: str) -> str:
    """Get recent news headlines associated with a company ticker."""
    try:
        news_items = yf.Ticker(symbol.upper()).news
        articles = []
        for item in news_items[:10]:
            content = item.get("content", item)
            articles.append({
                "title": content.get("title"),
                "summary": content.get("summary"),
                "publisher": (content.get("provider") or {}).get("displayName"),
                "link": (content.get("canonicalUrl") or {}).get("url"),
                "published": content.get("pubDate"),
            })
        return safe_json({"symbol": symbol.upper(), "news": articles})
    except Exception as error:
        return safe_json({"symbol": symbol.upper(), "error": f"News lookup failed: {error}"})

if __name__ == "__main__":
    mcp.run(transport="stdio")
