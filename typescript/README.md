# mcpward-sdk

TypeScript/JavaScript client SDK for the [mcpward](https://mcpward.redfleet.fr) MCP gateway.

## Install

```bash
npm install mcpward-sdk
```

## Usage

```typescript
import { MCPWardClient } from "mcpward-sdk";

const client = new MCPWardClient("https://mcpward.redfleet.fr", "mw_sk_your_key");

// List available tools
const tools = await client.listTools();
for (const tool of tools) {
  console.log(`${tool.name}: ${tool.description?.slice(0, 60)}`);
}

// Call a tool
const result = await client.callTool("read_wiki_structure", { repoName: "facebook/react" });
console.log(result.content);

// Call on a specific server
const issue = await client.callTool("create_issue", { title: "Bug" }, "github");

// Check health
const health = await client.health();

// Manage webhooks
const wh = await client.createWebhook("https://hooks.example.com", ["upstream.down"]);
const hooks = await client.listWebhooks();
await client.deleteWebhook(wh.id);

// Upgrade to Pro
const checkoutUrl = await client.createCheckout("pro");
```

## License

MIT
