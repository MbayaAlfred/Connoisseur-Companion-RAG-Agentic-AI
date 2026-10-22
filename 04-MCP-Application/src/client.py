"""Connoisseur Companion: MCP client discovery and tool demos (Module 4, Lesson 2)."""
import asyncio
import json
import os
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Root, TextContent, CreateMessageResult, CreateMessageRequestParams

SERVER_SCRIPT = str(Path(__file__).resolve().parent / "server.py")
PROJECT_DIR = Path(__file__).resolve().parents[2]
server_params = StdioServerParameters(command=sys.executable, args=[SERVER_SCRIPT])


def list_roots() -> list[Root]:
    """Advertise the project directory as a root (not an access-control sandbox)."""
    return [Root(uri=PROJECT_DIR.as_uri(), name=PROJECT_DIR.name)]


async def handle_sampling(params: CreateMessageRequestParams) -> CreateMessageResult:
    """Handle a server sampling request with Anthropic, if credentials are configured."""
    from anthropic import AsyncAnthropic
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is required when the server requests sampling.")
    prompt = params.messages[0].content.text
    print(f"\n[Sampling] Prompt preview: {prompt[:150]}...", file=sys.stderr)
    model = "claude-sonnet-4-20250514"
    response = await AsyncAnthropic().messages.create(
        model=model,
        max_tokens=params.maxTokens or 200,
        messages=[{"role": "user", "content": prompt}],
    )
    response_text = "\n".join(item.text for item in response.content if item.type == "text")
    return CreateMessageResult(role="assistant", content=TextContent(type="text", text=response_text), model=model)


async def call_tool(tool_name: str, arguments: dict) -> dict:
    """Connect, execute a server tool, and decode its JSON response."""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write, sampling_callback=handle_sampling, list_roots_callback=list_roots) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=arguments)
            if result.isError:
                raise RuntimeError(f"MCP tool error: {result.content}")
            return json.loads(result.content[0].text)


async def verify_connection():
    """Discover and verify the server's tools, resource and client-advertised roots."""
    print("=" * 60)
    print("MCP Connection Verification")
    print("=" * 60)
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write, sampling_callback=handle_sampling, list_roots_callback=list_roots) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            tool_names = [tool.name for tool in tools_result.tools]
            print("--- START SCREENSHOT ---")
            print(f"\nDiscovered {len(tool_names)} tools:")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {(tool.description or '')[:80]}...")
            for expected in ("get_restaurant_info", "recommend_by_vibe", "get_review"):
                assert expected in tool_names, f"FAIL: {expected} not found!"
            print("\nAll required tools verified!")
            resources_result = await session.list_resources()
            print(f"\nDiscovered {len(resources_result.resources)} resources:")
            for resource in resources_result.resources:
                print(f"  - {resource.uri}: {resource.name}")
            roots = list_roots()
            print(f"\nConfigured {len(roots)} roots:")
            for root in roots:
                print(f"  - {root.name}: {root.uri}")
            print("--- END SCREENSHOT ---")


async def demo_get_restaurant_info():
    print("\nDemo: get_restaurant_info('Iron & Embers')")
    print(json.dumps(await call_tool("get_restaurant_info", {"restaurant_name": "Iron & Embers"}), indent=2))


async def demo_recommend_by_vibe():
    print("\nDemo: recommend_by_vibe('moody')")
    data = await call_tool("recommend_by_vibe", {"vibe": "moody"})
    print(f"Vibe: {data['vibe_searched']}")
    print(f"Structured matches: {len(data['structured_matches'])}")
    for match in data["structured_matches"]:
        print(f"  - {match['name']} ({match['cuisine']}) - {match['rating']}/5")
    print(f"Raw text excerpts: {len(data['raw_text_excerpts'])}")


async def demo_get_review():
    print("\nDemo: get_review('Iron & Embers')")
    print(json.dumps(await call_tool("get_review", {"restaurant_name": "Iron & Embers"}), indent=2))


async def main():
    await demo_get_restaurant_info()
    await demo_recommend_by_vibe()
    await demo_get_review()
    await verify_connection()


if __name__ == "__main__":
    asyncio.run(main())
