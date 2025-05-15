import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp.client.stdio import StdioServerParameters

async def query_weather_server():
    # Setup how to launch your server process (weather.py)
    server_params = StdioServerParameters(
        command="python",
        args=["weather.py"]  # make sure this points to your server script
    )

    # Connect to the server process over stdio
    async with stdio_client(server_params) as (stdio, write):
        async with ClientSession(stdio, write) as session:
            await session.initialize()
            print("Connected to weather server.")

            # Example: call get_alerts tool with state="CA"
            response = await session.call_tool("get_alerts", {"state": "CA"})
            print("Weather Alerts for CA:")
            print(response.content)

            # Example: call get_forecast tool with latitude and longitude
            forecast = await session.call_tool("get_forecast", {"latitude": 37.77, "longitude": -122.42})
            print("\nWeather Forecast for (37.77, -122.42):")
            print(forecast.content)

if __name__ == "__main__":
    asyncio.run(query_weather_server())
