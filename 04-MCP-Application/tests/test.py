"""Lesson 1 MCP integration smoke test; run from repository root."""
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_SCRIPT = Path(__file__).resolve().parents[1] / "src" / "server.py"


async def run_test():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_SCRIPT)],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "get_restaurant_info", arguments={"restaurant_name": "Iron"}
            )
            if result.isError:
                raise RuntimeError(f"MCP tool error: {result.content}")
            print("\n--- START SCREENSHOT ---")
            print(result.content[0].text)
            print("--- END SCREENSHOT ---\n")


if __name__ == "__main__":
    asyncio.run(run_test())
