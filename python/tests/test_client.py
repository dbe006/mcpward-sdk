"""Test MCPWard SDK client."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcpward_sdk.client import MCPWardClient, MCPWardError, ToolResult


@pytest.fixture
def mock_response():
    def _make(status=200, json_data=None, text=None, content_type="application/json"):
        resp = MagicMock()
        resp.status_code = status
        resp.json.return_value = json_data or {}
        resp.text = text or json.dumps(json_data or {})
        resp.headers = {"content-type": content_type}
        return resp
    return _make


class TestListTools:
    @pytest.mark.asyncio
    async def test_list_tools_from_aggregated(self, mock_response):
        tools = [{"name": "read_file", "description": "Read a file"}]
        resp = mock_response(json_data={
            "jsonrpc": "2.0", "id": 1,
            "result": {"tools": tools},
        })

        client = MCPWardClient("https://test.com", "mw_sk_test")
        client._http = AsyncMock()
        client._http.post.return_value = resp

        result = await client.list_tools()
        assert len(result) == 1
        assert result[0]["name"] == "read_file"
        await client.close()

    @pytest.mark.asyncio
    async def test_list_tools_from_server(self, mock_response):
        resp = mock_response(json_data={
            "jsonrpc": "2.0", "id": 1,
            "result": {"tools": [{"name": "query"}]},
        })

        client = MCPWardClient("https://test.com", "mw_sk_test")
        client._http = AsyncMock()
        client._http.post.return_value = resp

        result = await client.list_tools(server="postgres")
        assert result[0]["name"] == "query"

        call_url = client._http.post.call_args[0][0]
        assert "/mcp/postgres" in call_url
        await client.close()


class TestCallTool:
    @pytest.mark.asyncio
    async def test_call_tool_success(self, mock_response):
        resp = mock_response(json_data={
            "jsonrpc": "2.0", "id": 1,
            "result": {"content": [{"type": "text", "text": "hello"}]},
        })

        client = MCPWardClient("https://test.com", "mw_sk_test")
        client._http = AsyncMock()
        client._http.post.return_value = resp

        result = await client.call_tool("greet", {"name": "world"})
        assert isinstance(result, ToolResult)
        assert result.content[0]["text"] == "hello"
        await client.close()

    @pytest.mark.asyncio
    async def test_call_tool_error_raises(self, mock_response):
        resp = mock_response(json_data={
            "jsonrpc": "2.0", "id": 1,
            "error": {"code": -32003, "message": "Permission denied"},
        })

        client = MCPWardClient("https://test.com", "mw_sk_test")
        client._http = AsyncMock()
        client._http.post.return_value = resp

        with pytest.raises(MCPWardError) as exc_info:
            await client.call_tool("delete_file", {})
        assert exc_info.value.code == -32003
        await client.close()


class TestSSEParsing:
    @pytest.mark.asyncio
    async def test_parse_sse_response(self, mock_response):
        sse_text = 'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"tools":[]}}\n\n'
        resp = mock_response(
            json_data=None,
            text=sse_text,
            content_type="text/event-stream",
        )

        client = MCPWardClient("https://test.com", "mw_sk_test")
        client._http = AsyncMock()
        client._http.post.return_value = resp

        tools = await client.list_tools()
        assert tools == []
        await client.close()


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_check(self, mock_response):
        resp = mock_response(json_data={"status": "ok"})

        client = MCPWardClient("https://test.com", "mw_sk_test")
        client._http = AsyncMock()
        client._http.get.return_value = resp

        result = await client.health()
        assert result["status"] == "ok"
        await client.close()


class TestContextManager:
    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        async with MCPWardClient("https://test.com", "mw_sk_test") as client:
            assert client.base_url == "https://test.com"
