import asyncio
import json
import logging
import time
from typing import Any, Callable

from simon.agent.events import AgentEvent
from simon.agent.response import AgentResponse, Usage
from simon.agent.structured import parse_structured, schema_instruction
from simon.exceptions import KnowledgeError, StructuredOutputError, ToolError
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
        max_steps: int = 6,
        on_event: Callable[[AgentEvent], None] | None = None,
    ) -> None:
        self.name = name
        self.system_prompt = system_prompt
        self.max_steps = max_steps
        self._router = ModelRouter()
        self._model_name = model
        self._on_event = on_event
        self.total_usage = Usage(0, 0, 0)
        if isinstance(memory, BaseMemory):
            self.memory: BaseMemory | None = memory
        elif memory:
            self.memory = InMemoryMemory()
        else:
            self.memory = None
        self.tools = ToolRegistry(tools)
        self.knowledge = KnowledgeBase() if knowledge else None

    def _emit(self, type_: str, **data: Any) -> None:
        if self._on_event is None:
            return
        try:
            self._on_event(AgentEvent(type=type_, data=data))
        except Exception:
            logger.warning("on_event hook raised an exception; ignoring")

    def _track_usage(self, response: AgentResponse) -> None:
        if response.usage:
            self.total_usage = self.total_usage + response.usage

    def run(self, prompt: str, output_model: type | None = None) -> AgentResponse:
        """Synchronous convenience API for beginners."""

        try:
            asyncio.get_running_loop()
            raise RuntimeError(
                "An event loop is already running. Use `await agent.run_async(...)`."
            )
        except RuntimeError as exc:
            if "already running" in str(exc):
                raise
        return asyncio.run(self.run_async(prompt, output_model=output_model))

    async def run_async(self, prompt: str, output_model: type | None = None) -> AgentResponse:
        t0 = time.perf_counter()
        model = self._router.resolve(self._model_name, task=prompt)
        logger.debug("run started | model=%s prompt_len=%d", type(model).__name__, len(prompt))
        self._emit("model_selected", model=type(model).__name__, model_id=getattr(model, "model", None))

        if self.memory:
            await self.memory.add("user", prompt)
            messages = await self.memory.list()
        else:
            messages = [{"role": "user", "content": prompt}]

        if self.system_prompt:
            messages = [{"role": "system", "content": self.system_prompt}] + messages

        if output_model is not None:
            messages.append({"role": "system", "content": schema_instruction(output_model)})

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

        schemas = self.tools.schemas()
        response = await with_retry(
            lambda: model.complete(messages=messages, tools=schemas),
            retries=settings.simon_max_retries,
            base_delay=settings.simon_retry_base_delay,
            timeout=settings.simon_request_timeout,
            on_retry=lambda attempt, exc: self._emit("retry_attempted", attempt=attempt, error=str(exc)),
        )
        self._track_usage(response)

        # ReAct loop: while the model requests tools, run them and feed the
        # results back until it produces a final answer (or max_steps is hit).
        step = 0
        while response.tool_calls and step < self.max_steps:
            step += 1
            messages.append(
                {
                    "role": "assistant",
                    "content": response.text,
                    "tool_calls": response.tool_calls,
                }
            )
            for call in response.tool_calls:
                logger.info("step %d | tool=%s", step, call.name)
                result = self._run_tool(call)
                self._emit("tool_called", tool=call.name, arguments=call.arguments, result=result[:200])
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": call.name,
                        "content": result,
                    }
                )
            response = await with_retry(
                lambda: model.complete(messages=messages, tools=schemas),
                retries=settings.simon_max_retries,
                base_delay=settings.simon_retry_base_delay,
                timeout=settings.simon_request_timeout,
                on_retry=lambda attempt, exc: self._emit("retry_attempted", attempt=attempt, error=str(exc)),
            )
            self._track_usage(response)

        if output_model is not None:
            for attempt in range(settings.simon_structured_retries + 1):
                try:
                    response.parsed = parse_structured(response.text, output_model)
                    break
                except Exception as exc:
                    if attempt >= settings.simon_structured_retries:
                        raise StructuredOutputError(
                            f"Model output did not match {output_model.__name__} after {attempt + 1} attempt(s): {exc}",
                            raw_text=response.text,
                            attempts=attempt + 1,
                        ) from exc
                    messages.append({"role": "assistant", "content": response.text})
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                f"That was not valid JSON for the schema. Error: {exc}. "
                                "Reply with ONLY the corrected JSON object, no prose."
                            ),
                        }
                    )
                    response = await with_retry(
                        lambda: model.complete(messages=messages, tools=schemas),
                        retries=settings.simon_max_retries,
                        base_delay=settings.simon_retry_base_delay,
                        timeout=settings.simon_request_timeout,
                    )
                    self._track_usage(response)

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

        self._emit("response_received", latency=elapsed, usage=response.usage, steps=step)
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
            raise ToolError("Tool arguments must be a JSON object.")

        result: Any = candidate(**args)
        return str(result)

    def _run_tool(self, call: Any) -> str:
        """Execute a model-requested tool call, returning its result as text.

        Errors (unknown tool, bad args, exceptions) are returned as strings so
        the model can see them and recover instead of the run crashing.
        """

        candidate = self.tools.get(call.name)
        if candidate is None:
            return (
                f"Error: tool '{call.name}' not found. "
                f"Available: {', '.join(self.tools.names())}"
            )
        try:
            return str(candidate(**call.arguments))
        except Exception as exc:  # noqa: BLE001 - surface error back to model
            return f"Error running tool '{call.name}': {exc}"

    def add_knowledge(self, path: str) -> int:
        """Index a file or folder into the knowledge base."""
        if self.knowledge is None:
            raise KnowledgeError("Agent was created with knowledge=False.")
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
