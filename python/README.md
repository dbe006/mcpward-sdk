# mcpward-sdk

Python client SDK for the [mcpward](https://mcpward.redfleet.fr) MCP gateway.

## Install

```bash
pip install mcpward-sdk
```

## Usage

```python
from mcpward_sdk import MCPWardClient

async with MCPWardClient("https://mcpward.redfleet.fr", "mw_sk_your_key") as client:
    # List available tools
    tools = await client.list_tools()
    for tool in tools:
        print(f"{tool['name']}: {tool.get('description', '')[:60]}")

    # Call a tool
    result = await client.call_tool("read_wiki_structure", {"repoName": "facebook/react"})
    print(result.content)

    # Call a tool on a specific server
    result = await client.call_tool("create_issue", {"title": "Bug"}, server="github")

    # Check health
    health = await client.health()

    # Manage webhooks
    wh = await client.create_webhook("https://hooks.example.com/mcpward", ["upstream.down"])
    hooks = await client.list_webhooks()
    await client.delete_webhook(wh["id"])

    # Upgrade to Pro
    checkout_url = await client.create_checkout("pro")
```

## License

MIT
