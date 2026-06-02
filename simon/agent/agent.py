import asyncio
import json
from pathlib import Path
from typing import Any

from simon.knowledge import KnowledgeBase
from simon.memory import InMemoryMemory
from simon.router import ModelRouter
from simon.tools import ToolRegistry

_DEFAULT_KNOWLEDGE_DIRS = [
    Path.home() / "Documents",
    Path.home() / "Downloads",
]


class Agent:
    """Minimal agent API with optional memory, knowledge, and tools."""

    def __init__(
        self,
        model: str | None = None,
        memory: bool = False,
        tools: list[object] | None = None,
        knowledge: bool = True,
    ) -> None:
        self._router = ModelRouter()
        self._model_name = model
        self.memory = InMemoryMemory() if memory else None
        self.tools = ToolRegistry(tools)
        self.knowledge = KnowledgeBase() if knowledge else None
        if self.knowledge:
            for d in _DEFAULT_KNOWLEDGE_DIRS:
                if d.exists():
                    self.knowledge.add(str(d))

    def run(self, prompt: str) -> str:
        """Synchronous convenience API for beginners."""

        try:
            asyncio.get_running_loop()
            raise RuntimeError(
                "An event loop is already running. Use `await agent.run_async(...)`."
            )
        except RuntimeError as exc:
            if "already running" in str(exc):
                raise
        return asyncio.run(self.run_async(prompt))

    async def run_async(self, prompt: str) -> str:
        if self.memory:
            await self.memory.add("user", prompt)
            messages = await self.memory.list()
        else:
            messages = [{"role": "user", "content": prompt}]

        tool_response = await self._maybe_call_tool(prompt)
        if tool_response is not None:
            if self.memory:
                await self.memory.add("assistant", tool_response)
            return tool_response

        context = self._knowledge_context(prompt)
        if context:
            messages.append({"role": "system", "content": context})

        model = self._router.resolve(self._model_name, task=prompt)
        response = await model.complete(messages=messages, tools=self.tools.schemas())

        if self.memory:
            await self.memory.add("assistant", response)

        return response

    async def _maybe_call_tool(self, prompt: str) -> str | None:
        """Support a tiny explicit tool call format: tool:name {json_args}."""

        text = prompt.strip()
        if not text.startswith("tool:"):
            return None

        remainder = text[5:].strip()
        if " " in remainder:
            name, raw_args = remainder.split(" ", 1)
            args = json.loads(raw_args)
        else:
            name, args = remainder, {}

        candidate = self.tools.get(name)
        if candidate is None:
            return (
                f"Tool '{name}' not found. Available: {', '.join(self.tools.names())}"
            )

        if not isinstance(args, dict):
            raise ValueError("Tool arguments must be a JSON object.")

        result: Any = candidate(**args)
        return str(result)

    def _knowledge_context(self, prompt: str) -> str:
        if not self.knowledge:
            return ""
        hits = self.knowledge.search(prompt, top_k=2)
        if not hits:
            return ""

        lines = ["Relevant knowledge:"]
        for hit in hits:
            lines.append(f"- ({hit['source']}) {hit['text']}")
        return "\n".join(lines)
