# mcpward — public SDKs, examples, schemas

Client libraries, examples, audit log schema, and signature verifier for the [mcpward](https://mcpward.redfleet.fr) MCP gateway.

mcpward is a reverse proxy + control plane for MCP servers. It sits between your AI agents and your MCP servers and handles auth, audit, and observability so you don't have to bolt them onto each server individually.

This repository contains the open-source integration layer. The gateway service itself is hosted at [mcpward.redfleet.fr](https://mcpward.redfleet.fr).

## What's in here

| Folder | Description |
|---|---|
| [`python/`](python/) | Python client SDK — `pip install mcpward-sdk` |
| [`typescript/`](typescript/) | TypeScript / JavaScript client SDK — `npm install mcpward-sdk` |
| [`examples/`](examples/) | Claude Desktop config, Cursor config, AgentKit example |
| [`schemas/`](schemas/) | JSON Schema for the signed audit log format |
| [`tools/`](tools/) | Stand-alone CLI that verifies Ed25519-signed audit log records — `pipx install mcpward-verify` |

## Quick start

### 1. Get an API key

The hosted service issues free keys. See [mcpward.redfleet.fr](https://mcpward.redfleet.fr) for details.

### 2. Point your MCP client at mcpward

**Claude Desktop** — add to your MCP config (see [`examples/claude_desktop_config.json`](examples/claude_desktop_config.json)):

```json
{
  "mcpServers": {
    "mcpward": {
      "transport": "streamable-http",
      "url": "https://mcpward.redfleet.fr/mcp",
      "headers": { "Authorization": "Bearer mw_sk_YOUR_API_KEY" }
    }
  }
}
```

**Cursor** — add to `.cursor/mcp.json` (see [`examples/cursor_mcp.json`](examples/cursor_mcp.json)).

**Python agent** — use the SDK:

```python
from mcpward_sdk import MCPWardClient

async with MCPWardClient("https://mcpward.redfleet.fr", "mw_sk_your_key") as client:
    tools = await client.list_tools()
    result = await client.call_tool("read_wiki_structure", {"repoName": "facebook/react"})
```

**TypeScript agent**:

```typescript
import { MCPWardClient } from "mcpward-sdk";

const client = new MCPWardClient("https://mcpward.redfleet.fr", "mw_sk_your_key");
const tools = await client.listTools();
```

## Audit log verification

Every request through the gateway produces an Ed25519-signed audit record (see [`schemas/audit_log_v1.json`](schemas/audit_log_v1.json) for the format). You can verify the signature off-band with the stand-alone CLI:

```bash
pipx install mcpward-verify
mcpward-verify --pubkey ed25519.pub --record record.json
mcpward-verify --pubkey ed25519.pub --batch records.jsonl
```

The gateway publishes its public key at `https://mcpward.redfleet.fr/v1/pubkey` so anyone can audit a record without contacting the operator.

## Self-hosted gateway

The gateway core (proxy, RBAC engine, audit storage, OAuth lifecycle, billing) is closed source. Contact mcpward@redfleet.fr for self-hosted deployments.

## License

MIT — see [LICENSE](LICENSE).
