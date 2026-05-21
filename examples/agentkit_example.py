"""Minimal example: calling MCP tools through mcpward gateway."""

import asyncio

import httpx

MCPWARD_URL = "https://mcpward.redfleet.fr/mcp"
MCPWARD_KEY = "mw_sk_YOUR_API_KEY_HERE"


async def list_tools() -> list[dict]:
    """List all available tools through the aggregated endpoint."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            MCPWARD_URL,
            headers={"Authorization": f"Bearer {MCPWARD_KEY}"},
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
        )
        data = resp.json()
        return data.get("result", {}).get("tools", [])


async def call_tool(tool_name: str, arguments: dict) -> dict:
    """Call a specific tool through the mcpward gateway."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            MCPWARD_URL,
            headers={"Authorization": f"Bearer {MCPWARD_KEY}"},
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            },
        )
        return resp.json()


async def main():
    # List available tools
    tools = await list_tools()
    print(f"Available tools ({len(tools)}):")
    for tool in tools:
        print(f"  - {tool['name']}: {tool.get('description', '')[:60]}")

    # Call a tool (example)
    if tools:
        result = await call_tool(tools[0]["name"], {})
        print(f"\nResult: {result}")


if __name__ == "__main__":
    asyncio.run(main())
