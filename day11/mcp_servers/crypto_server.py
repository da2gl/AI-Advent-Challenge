"""MCP server for cryptocurrency data using CoinGecko API."""

import json
import requests
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("Crypto Data Server")


def _fetch_coingecko(endpoint: str, params: dict = None) -> dict:
    """Fetch data from CoinGecko API.

    Args:
        endpoint: API endpoint
        params: Query parameters

    Returns:
        API response as dictionary

    Raises:
        Exception: If API request fails
    """
    base_url = "https://api.coingecko.com/api/v3"
    url = f"{base_url}/{endpoint}"

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"CoinGecko API error: {str(e)}")


@mcp.tool()
def get_crypto_prices(
    limit: int = 10,
    currency: str = "usd"
) -> str:
    """Get current prices for top cryptocurrencies.

    Args:
        limit: Number of cryptocurrencies to return (default: 10, max: 250)
        currency: Currency for prices (default: usd)

    Returns:
        JSON string with cryptocurrency prices
    """
    params = {
        "vs_currency": currency,
        "order": "market_cap_desc",
        "per_page": min(limit, 250),
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "24h"
    }

    data = _fetch_coingecko("coins/markets", params)

    # Format results
    results = []
    for coin in data:
        results.append({
            "name": coin["name"],
            "symbol": coin["symbol"].upper(),
            "current_price": coin["current_price"],
            "market_cap": coin["market_cap"],
            "price_change_24h": coin.get("price_change_percentage_24h"),
            "rank": coin["market_cap_rank"]
        })

    return json.dumps(results, indent=2)


@mcp.tool()
def get_crypto_by_symbol(
    symbol: str,
    currency: str = "usd"
) -> str:
    """Get detailed information for a specific cryptocurrency by symbol.

    Args:
        symbol: Cryptocurrency symbol (e.g., btc, eth, sol)
        currency: Currency for prices (default: usd)

    Returns:
        JSON string with cryptocurrency details
    """
    # Search for coin by symbol
    search_data = _fetch_coingecko("search", {"query": symbol})

    coin_id = None
    for coin in search_data.get("coins", []):
        if coin["symbol"].lower() == symbol.lower():
            coin_id = coin["id"]
            break

    if not coin_id:
        return json.dumps({"error": f"Cryptocurrency with symbol '{symbol}' not found"})

    # Get detailed data
    params = {
        "localization": False,
        "tickers": False,
        "market_data": True,
        "community_data": False,
        "developer_data": False
    }

    data = _fetch_coingecko(f"coins/{coin_id}", params)

    # Format result
    market_data = data.get("market_data", {})
    result = {
        "name": data["name"],
        "symbol": data["symbol"].upper(),
        "current_price": market_data.get("current_price", {}).get(currency),
        "market_cap": market_data.get("market_cap", {}).get(currency),
        "total_volume": market_data.get("total_volume", {}).get(currency),
        "price_change_24h": market_data.get("price_change_percentage_24h"),
        "price_change_7d": market_data.get("price_change_percentage_7d"),
        "price_change_30d": market_data.get("price_change_percentage_30d"),
        "high_24h": market_data.get("high_24h", {}).get(currency),
        "low_24h": market_data.get("low_24h", {}).get(currency),
        "ath": market_data.get("ath", {}).get(currency),
        "ath_date": market_data.get("ath_date", {}).get(currency)
    }

    return json.dumps(result, indent=2)


@mcp.tool()
def get_trending_crypto() -> str:
    """Get currently trending cryptocurrencies.

    Returns:
        JSON string with trending cryptocurrencies
    """
    data = _fetch_coingecko("search/trending")

    results = []
    for item in data.get("coins", []):
        coin = item.get("item", {})
        results.append({
            "name": coin.get("name"),
            "symbol": coin.get("symbol"),
            "market_cap_rank": coin.get("market_cap_rank"),
            "price_btc": coin.get("price_btc")
        })

    return json.dumps(results, indent=2)


@mcp.tool()
def get_market_summary(currency: str = "usd") -> str:
    """Get global cryptocurrency market summary.

    Args:
        currency: Currency for values (default: usd)

    Returns:
        JSON string with market summary
    """
    data = _fetch_coingecko("global")
    global_data = data.get("data", {})

    result = {
        "total_market_cap": global_data.get("total_market_cap", {}).get(currency),
        "total_volume_24h": global_data.get("total_volume", {}).get(currency),
        "market_cap_percentage": global_data.get("market_cap_percentage", {}),
        "active_cryptocurrencies": global_data.get("active_cryptocurrencies"),
        "markets": global_data.get("markets"),
        "market_cap_change_24h": global_data.get("market_cap_change_percentage_24h_usd")
    }

    return json.dumps(result, indent=2)


if __name__ == "__main__":
    # Run the MCP server
    mcp.run(show_banner=False)
