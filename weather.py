from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import sys
import asyncio

# Initialize FastMCP server
print("Initializing FastMCP server...", file=sys.stderr)
mcp = FastMCP("weather", version="1.0.0")
print("FastMCP server initialized with name: 'weather'", file=sys.stderr)

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    print(f"Making request to: {url}", file=sys.stderr)
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            print(f"Request successful - Status code: {response.status_code}", file=sys.stderr)
            return response.json()
        except Exception as e:
            print(f"ERROR: {str(e)}", file=sys.stderr)
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    print(f"Formatting alert with ID: {feature.get('id', 'unknown')}", file=sys.stderr)
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state."""
    print(f"Tool called: get_alerts({state})", file=sys.stderr)
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data:
        print(f"ERROR: Failed to fetch alerts for state: {state}", file=sys.stderr)
        return "Unable to fetch alerts or no alerts found."

    if "features" not in data:
        print(f"ERROR: Invalid response format - 'features' key missing for state: {state}", file=sys.stderr)
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        print(f"No active alerts found for state: {state}", file=sys.stderr)
        return "No active alerts for this state."

    print(f"Found {len(data['features'])} alerts for state: {state}", file=sys.stderr)
    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location."""
    print(f"Tool called: get_forecast({latitude}, {longitude})", file=sys.stderr)
    
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        print(f"ERROR: Failed to fetch points data for coordinates: ({latitude}, {longitude})", file=sys.stderr)
        return "Unable to fetch forecast data for this location."

    forecast_url = points_data["properties"]["forecast"]
    print(f"Fetching detailed forecast from: {forecast_url}", file=sys.stderr)
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        print(f"ERROR: Failed to fetch forecast data from: {forecast_url}", file=sys.stderr)
        return "Unable to fetch detailed forecast."

    periods = forecast_data["properties"]["periods"]
    print(f"Processing {len(periods[:5])} forecast periods", file=sys.stderr)
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

if __name__ == "__main__":
    print("Starting weather service on stdio transport...", file=sys.stderr)
    try:
        asyncio.run(mcp.run(transport='stdio'))
    except KeyboardInterrupt:
        print("Weather service stopped by user.", file=sys.stderr)
    except Exception as e:
        print(f"ERROR: Failed to start MCP server: {str(e)}", file=sys.stderr)
    finally: 
        print("Weather service stopped.", file=sys.stderr)