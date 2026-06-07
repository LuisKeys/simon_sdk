"""Minimal MCP server for local testing. Run with: python mcp_example_server.py"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("simon-example")


@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two integers and return their sum."""
    return a + b


@mcp.tool()
def reverse_string(text: str) -> str:
    """Reverse the characters in a string."""
    return text[::-1]


if __name__ == "__main__":
    mcp.run(transport="stdio")
