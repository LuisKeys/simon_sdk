import asyncio
import json
import logging
import time
from typing import Any

from simon.agent.response import AgentResponse, Usage
from simon.knowledge import KnowledgeBase
from simon.memory import BaseMemory, InMemoryMemory
from simon.config import settings
from simon.reliability import with_retry
from simon.router import ModelRouter
from simon.tools import ToolRegistry

logger = logging.getLogger("simon.agent")


def _enabled_knowledge_dirs() -> list:
    from pathlib import Path

    mapping = [
        (settings.enable_dir_documents, Path.home() / "Documents"),
        (settings.enable_dir_downloads, Path.home() / "Downloads"),
        (settings.enable_dir_pictures, Path.home() / "Pictures"),
        (settings.enable_dir_desktop, Path.home() / "Desktop"),
    ]
    return [path for enabled, path in mapping if enabled]


class Agent:
    """Minimal agent API with optional memory, knowledge, and tools."""

    def __init__(
        self,
        model: str | None = None,
        memory: bool | BaseMemory = False,
        tools: list[object] | None = None,
        knowledge: bool = True,
        name: str = "Simon",
        system_prompt: str | None = None,
    ) -> None:
        self.name = name
        self.system_prompt = system_prompt
        self._router = ModelRouter()
        self._model_name = model
        if isinstance(memory, BaseMemory):
            self.memory: BaseMemory | None = memory
        elif memory:
            self.memory = InMemoryMemory()
        else:
            self.memory = None
        self.tools = ToolRegistry(tools)
        self.knowledge = KnowledgeBase() if knowledge else None

    def run(self, prompt: str) -> AgentResponse:
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

    async def run_async(self, prompt: str) -> AgentResponse:
        t0 = time.perf_counter()
        model = self._router.resolve(self._model_name, task=prompt)
        logger.debug("run started | model=%s prompt_len=%d", type(model).__name__, len(prompt))

        if self.memory:
            await self.memory.add("user", prompt)
            messages = await self.memory.list()
        else:
            messages = [{"role": "user", "content": prompt}]

        if self.system_prompt:
            messages = [{"role": "system", "content": self.system_prompt}] + messages

        tool_response = await self._maybe_call_tool(prompt)
        if tool_response is not None:
            if self.memory:
                await self.memory.add("assistant", tool_response)
            elapsed = time.perf_counter() - t0
            logger.info("run completed (tool) | latency=%.2fs", elapsed)
            return AgentResponse(text=tool_response)

        context = self._knowledge_context(prompt)
        if context:
            messages.append({"role": "system", "content": context})

        response = await with_retry(
            lambda: model.complete(messages=messages, tools=self.tools.schemas()),
            retries=settings.simon_max_retries,
            base_delay=settings.simon_retry_base_delay,
            timeout=settings.simon_request_timeout,
        )

        if self.memory:
            await self.memory.add("assistant", response.text)

        elapsed = time.perf_counter() - t0
        if response.usage:
            logger.info(
                "run completed | latency=%.2fs input_tokens=%d output_tokens=%d total=%d",
                elapsed,
                response.usage.input_tokens,
                response.usage.output_tokens,
                response.usage.total_tokens,
            )
        else:
            logger.info("run completed | latency=%.2fs", elapsed)

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

    def add_knowledge(self, path: str) -> int:
        """Index a file or folder into the knowledge base."""
        if self.knowledge is None:
            raise RuntimeError("Agent was created with knowledge=False.")
        return self.knowledge.add(path)

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
