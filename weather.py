# weather.py
import httpx
import sys
import logging
from mcp.server.fastmcp import FastMCP

# NEVER use print() — log to stderr only
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

mcp = FastMCP("Weather PoC Server")

NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "mcp-weather-poc/1.0 (gaurav@example.com)"

async def fetch_nws(url: str) -> dict:
    """Helper to call the NWS API."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=headers, timeout=10.0)
        r.raise_for_status()
        return r.json()

@mcp.tool()
async def get_alerts(state: str) -> str:
    """
    Get active weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. 'CA', 'NY', 'TX')
    """
    logging.info(f"Fetching alerts for state: {state}")
    data = await fetch_nws(f"{NWS_API_BASE}/alerts/active?area={state}")
    features = data.get("features", [])
    if not features:
        return f"No active alerts for {state}."
    alerts = []
    for f in features[:5]:  # cap at 5
        p = f.get("properties", {})
        alerts.append(
            f"Event: {p.get('event')}\n"
            f"Area: {p.get('areaDesc')}\n"
            f"Severity: {p.get('severity')}\n"
            f"Headline: {p.get('headline')}\n"
        )
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """
    Get a 7-day weather forecast for a location using coordinates.

    Args:
        latitude: Latitude of the location (e.g. 40.7128 for New York)
        longitude: Longitude of the location (e.g. -74.0060 for New York)
    """
    logging.info(f"Fetching forecast for ({latitude}, {longitude})")
    # Step 1: resolve grid point
    point_data = await fetch_nws(f"{NWS_API_BASE}/points/{latitude},{longitude}")
    forecast_url = point_data["properties"]["forecast"]
    # Step 2: fetch forecast
    forecast_data = await fetch_nws(forecast_url)
    periods = forecast_data["properties"]["periods"][:6]
    result = []
    for p in periods:
        result.append(
            f"{p['name']}: {p['detailedForecast']}"
        )
    return "\n\n".join(result)

if __name__ == "__main__":
    mcp.run(transport="stdio")
