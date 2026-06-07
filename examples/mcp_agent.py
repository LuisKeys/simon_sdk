"""Example: using tools from an MCP server inside a Simon agent."""

import os
import sys

# Allow running from the repo root without installing the package.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from simon import Agent
from simon.tools.mcp_client import MCPClient

SERVER = [sys.executable, "simon/tools/builtin/mcp_example_server.py"]

client = MCPClient(SERVER)
tools = client.get_tools()

print(f"Tools loaded from MCP server: {[t.name for t in tools]}\n")

agent = Agent(tools=tools)

response = agent.run("Use the add_numbers tool to compute 37 + 5, then reverse the result string.")
print(response.text)
