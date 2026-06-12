import asyncio

import pytest

from simon import Agent, AgentEvent
from simon.agent.response import AgentResponse, ToolCall, Usage
from simon.models.base import BaseModel
from simon.reliability import with_retry
from simon.tools.tool import tool


@tool
def echo_tool(msg: str) -> str:
    """Echo a message back."""
    return msg


class ScriptedModel(BaseModel):
    def __init__(self, responses: list[AgentResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[list[dict]] = []

    async def complete(self, messages, tools=None) -> AgentResponse:
        self.calls.append(list(messages))
        if self._responses:
            return self._responses.pop(0)
        return AgentResponse(text="done")


def _use_model(agent: Agent, model: BaseModel) -> None:
    agent._router.resolve = lambda *a, **k: model  # type: ignore[assignment]


# --- Hooks ---

def test_events_emitted_in_order():
    model = ScriptedModel([
        AgentResponse(
            text="",
            tool_calls=[ToolCall(id="t1", name="echo_tool", arguments={"msg": "hi"})],
        ),
        AgentResponse(text="done"),
    ])
    events: list[AgentEvent] = []
    agent = Agent(tools=[echo_tool], knowledge=False, on_event=events.append)
    _use_model(agent, model)

    agent.run("test")

    types = [e.type for e in events]
    assert types[0] == "model_selected"
    assert "tool_called" in types
    assert types[-1] == "response_received"


def test_model_selected_data():
    model = ScriptedModel([AgentResponse(text="hi")])
    events: list[AgentEvent] = []
    agent = Agent(knowledge=False, on_event=events.append)
    _use_model(agent, model)

    agent.run("hello")

    sel = next(e for e in events if e.type == "model_selected")
    assert "model" in sel.data


def test_tool_called_data():
    model = ScriptedModel([
        AgentResponse(
            text="",
            tool_calls=[ToolCall(id="t1", name="echo_tool", arguments={"msg": "hello"})],
        ),
        AgentResponse(text="done"),
    ])
    events: list[AgentEvent] = []
    agent = Agent(tools=[echo_tool], knowledge=False, on_event=events.append)
    _use_model(agent, model)

    agent.run("call echo")

    tc = next(e for e in events if e.type == "tool_called")
    assert tc.data["tool"] == "echo_tool"
    assert "result" in tc.data


def test_buggy_hook_does_not_crash_run():
    def bad_hook(e: AgentEvent) -> None:
        raise ZeroDivisionError("boom")

    model = ScriptedModel([AgentResponse(text="ok")])
    agent = Agent(knowledge=False, on_event=bad_hook)
    _use_model(agent, model)

    out = agent.run("hello")
    assert out.text == "ok"


def test_no_hook_does_not_crash():
    model = ScriptedModel([AgentResponse(text="hi")])
    agent = Agent(knowledge=False)
    _use_model(agent, model)

    out = agent.run("hello")
    assert out.text == "hi"


# --- Usage tracking ---

def test_total_usage_accumulates():
    usage = Usage(input_tokens=10, output_tokens=5, total_tokens=15)
    model = ScriptedModel([
        AgentResponse(text="first", usage=usage),
        AgentResponse(text="second", usage=usage),
    ])
    agent = Agent(knowledge=False)
    _use_model(agent, model)

    agent.run("first run")
    # reload model responses for second run
    model._responses = [AgentResponse(text="second", usage=usage)]
    agent.run("second run")

    assert agent.total_usage.total_tokens == 30
    assert agent.total_usage.input_tokens == 20
    assert agent.total_usage.output_tokens == 10


def test_total_usage_react_accumulates():
    usage = Usage(input_tokens=5, output_tokens=5, total_tokens=10)
    model = ScriptedModel([
        AgentResponse(
            text="",
            usage=usage,
            tool_calls=[ToolCall(id="t1", name="echo_tool", arguments={"msg": "hi"})],
        ),
        AgentResponse(text="done", usage=usage),
    ])
    agent = Agent(tools=[echo_tool], knowledge=False)
    _use_model(agent, model)

    agent.run("run with tool")

    # Both model calls tracked
    assert agent.total_usage.total_tokens == 20


# --- on_retry in reliability ---

def test_on_retry_called_on_failure():
    calls = {"n": 0}
    retries_seen: list[tuple[int, BaseException]] = []

    async def factory():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("transient")
        return "ok"

    asyncio.run(
        with_retry(
            factory,
            retries=3,
            base_delay=0.0,
            timeout=None,
            on_retry=lambda attempt, exc: retries_seen.append((attempt, exc)),
        )
    )

    assert len(retries_seen) == 2
    assert retries_seen[0][0] == 1
    assert retries_seen[1][0] == 2


def test_on_retry_not_called_on_first_success():
    retries_seen: list = []

    async def factory():
        return "immediate"

    asyncio.run(
        with_retry(
            factory,
            retries=2,
            base_delay=0.0,
            timeout=None,
            on_retry=lambda a, e: retries_seen.append(a),
        )
    )

    assert retries_seen == []
