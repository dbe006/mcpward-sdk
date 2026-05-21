"""MCPWard client — interact with mcpward gateway from Python."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class MCPWardError(Exception):
    code: int
    message: str
    data: dict | None = None

    def __str__(self) -> str:
        return f"MCPWardError({self.code}): {self.message}"


@dataclass
class ToolResult:
    content: list[dict]
    raw: dict


class MCPWardClient:
    """Client for the mcpward MCP gateway.

    Usage:
        client = MCPWardClient("https://mcpward.redfleet.fr", "mw_sk_your_key")

        # List available tools
        tools = await client.list_tools()

        # Call a tool
        result = await client.call_tool("read_file", {"path": "/etc/hostname"})

        # Call a tool on a specific server
        result = await client.call_tool("create_issue", {"title": "Bug"}, server="github")

        # Get usage stats
        usage = await client.get_usage()

        # Manage webhooks
        wh = await client.create_webhook("https://hooks.example.com", ["upstream.down"])
        hooks = await client.list_webhooks()
        await client.delete_webhook(wh["id"])
    """

    def __init__(
        self,
        base_url: str = "https://mcpward.redfleet.fr",
        api_key: str = "",
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._http = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
        )

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> MCPWardClient:
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    # --- JSON-RPC helpers ---

    async def _jsonrpc(
        self, method: str, params: dict | None = None, server: str | None = None
    ) -> dict:
        """Send a JSON-RPC request through mcpward."""
        url = f"{self.base_url}/mcp/{server}" if server else f"{self.base_url}/mcp"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {},
        }
        resp = await self._http.post(url, json=payload)
        data = self._parse_response(resp)

        if "error" in data:
            err = data["error"]
            raise MCPWardError(
                code=err.get("code", -1),
                message=err.get("message", "Unknown error"),
                data=err.get("data"),
            )
        return data

    def _parse_response(self, resp: httpx.Response) -> dict:
        """Parse JSON or SSE response."""
        content_type = resp.headers.get("content-type", "")
        text = resp.text

        if "text/event-stream" in content_type:
            for line in reversed(text.strip().splitlines()):
                if line.startswith("data: "):
                    import json
                    return json.loads(line[6:])
                if line.startswith("data:"):
                    import json
                    return json.loads(line[5:])
            raise MCPWardError(code=-1, message="No data in SSE response")

        return resp.json()

    # --- REST helpers ---

    async def _get(self, path: str) -> dict:
        resp = await self._http.get(f"{self.base_url}{path}")
        if resp.status_code >= 400:
            data = resp.json()
            raise MCPWardError(code=resp.status_code, message=data.get("error", str(data)))
        return resp.json()

    async def _post(self, path: str, body: dict) -> dict:
        resp = await self._http.post(f"{self.base_url}{path}", json=body)
        if resp.status_code >= 400:
            data = resp.json()
            raise MCPWardError(code=resp.status_code, message=data.get("error", str(data)))
        return resp.json()

    async def _delete(self, path: str) -> dict:
        resp = await self._http.delete(f"{self.base_url}{path}")
        if resp.status_code >= 400:
            data = resp.json()
            raise MCPWardError(code=resp.status_code, message=data.get("error", str(data)))
        return resp.json()

    # --- MCP operations ---

    async def list_tools(self, server: str | None = None) -> list[dict]:
        """List available tools (from one server or aggregated)."""
        data = await self._jsonrpc("tools/list", server=server)
        return data.get("result", {}).get("tools", [])

    async def call_tool(
        self, tool_name: str, arguments: dict | None = None, server: str | None = None
    ) -> ToolResult:
        """Call a tool through the gateway."""
        params = {"name": tool_name, "arguments": arguments or {}}
        data = await self._jsonrpc("tools/call", params=params, server=server)
        result = data.get("result", {})
        return ToolResult(
            content=result.get("content", []),
            raw=result,
        )

    # --- Usage ---

    async def get_usage(self) -> dict:
        """Get usage stats for this key."""
        # Extract key_id from a lightweight call — or use the key_id if known
        # For now, this requires knowing the key_id
        raise NotImplementedError(
            "Use client.get_usage_by_id(key_id) — key_id is returned at provisioning time"
        )

    async def get_usage_by_id(self, key_id: str) -> dict:
        """Get usage stats for a specific key."""
        return await self._get(f"/v1/usage/key/{key_id}")

    # --- Webhooks ---

    async def create_webhook(
        self, url: str, events: list[str] | None = None
    ) -> dict:
        """Register a webhook endpoint."""
        body: dict[str, Any] = {"url": url}
        if events:
            body["events"] = events
        return await self._post("/v1/webhooks", body)

    async def list_webhooks(self) -> list[dict]:
        """List active webhooks."""
        data = await self._get("/v1/webhooks")
        return data.get("webhooks", [])

    async def delete_webhook(self, webhook_id: str) -> dict:
        """Delete a webhook."""
        return await self._delete(f"/v1/webhooks/{webhook_id}")

    # --- Billing ---

    async def create_checkout(self, tier: str) -> str:
        """Create a Stripe checkout session. Returns checkout URL."""
        data = await self._post("/v1/billing/checkout", {"tier": tier})
        return data["checkout_url"]

    # --- Health ---

    async def health(self) -> dict:
        """Check gateway health."""
        return await self._get("/healthz")

    async def server_health(self, server: str) -> dict:
        """Check upstream server health."""
        return await self._get(f"/mcp/{server}/health")
