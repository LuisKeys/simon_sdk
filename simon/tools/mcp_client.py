"""MCP client: connect to an MCP server and expose its tools as Simon Tool objects."""

import asyncio
from contextlib import AsyncExitStack
from typing import Any

from simon.tools.tool import Tool


class MCPClient:
    """Connect to an MCP server via stdio and retrieve its tools."""

    def __init__(self, command: list[str]) -> None:
        self._command = command

    async def get_tools_async(self) -> list[Tool]:
        from mcp import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        server_params = StdioServerParameters(
            command=self._command[0],
            args=self._command[1:],
        )

        async with AsyncExitStack() as stack:
            read, write = await stack.enter_async_context(stdio_client(server_params))
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            result = await session.list_tools()

        return [self._make_tool(mcp_tool) for mcp_tool in result.tools]

    def get_tools(self) -> list[Tool]:
        """Synchronous wrapper around get_tools_async."""
        return asyncio.run(self.get_tools_async())

    def _make_tool(self, mcp_tool: Any) -> Tool:
        name = mcp_tool.name
        description = mcp_tool.description or f"Tool {name}"
        schema = mcp_tool.inputSchema or {"type": "object", "properties": {}, "required": []}
        command = self._command

        async def _call_async(**kwargs: Any) -> str:
            from mcp import ClientSession
            from mcp.client.stdio import StdioServerParameters, stdio_client

            params = StdioServerParameters(command=command[0], args=command[1:])
            async with AsyncExitStack() as stack:
                read, write = await stack.enter_async_context(stdio_client(params))
                s = await stack.enter_async_context(ClientSession(read, write))
                await s.initialize()
                call_result = await s.call_tool(name, kwargs)
            parts = [c.text for c in call_result.content if hasattr(c, "text")]
            return "\n".join(parts)

        def _call_sync(**kwargs: Any) -> str:
            return asyncio.run(_call_async(**kwargs))

        return Tool(name=name, description=description, fn=_call_sync, schema=schema)
