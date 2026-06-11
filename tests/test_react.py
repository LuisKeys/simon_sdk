from simon import Agent, tool
from simon.agent.response import AgentResponse, ToolCall
from simon.models.base import BaseModel


@tool
def add_numbers(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


class ScriptedModel(BaseModel):
    """Returns a queued AgentResponse per call and records messages seen."""

    def __init__(self, responses: list[AgentResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[list[dict]] = []

    async def complete(self, messages, tools=None) -> AgentResponse:
        self.calls.append(messages)
        if self._responses:
            return self._responses.pop(0)
        return AgentResponse(text="done")


def _use_model(agent: Agent, model: BaseModel) -> None:
    agent._router.resolve = lambda *a, **k: model  # type: ignore[assignment]


def test_react_loop_executes_tool_and_finishes() -> None:
    model = ScriptedModel(
        [
            AgentResponse(
                text="",
                tool_calls=[ToolCall(id="c1", name="add_numbers", arguments={"a": 2, "b": 3})],
            ),
            AgentResponse(text="The sum is 5."),
        ]
    )
    agent = Agent(tools=[add_numbers], knowledge=False)
    _use_model(agent, model)

    out = agent.run("add 2 and 3")

    assert out.text == "The sum is 5."
    assert len(model.calls) == 2
    # Second call must include the tool result fed back to the model.
    second = model.calls[1]
    assert any(m["role"] == "tool" and m["content"] == "5" for m in second)


def test_react_loop_respects_max_steps() -> None:
    # Model always asks for a tool -> would loop forever without the cap.
    always = AgentResponse(
        text="",
        tool_calls=[ToolCall(id="c", name="add_numbers", arguments={"a": 1, "b": 1})],
    )
    model = ScriptedModel([always] * 20)
    agent = Agent(tools=[add_numbers], knowledge=False, max_steps=3)
    _use_model(agent, model)

    agent.run("loop")

    # Initial call + max_steps follow-ups.
    assert len(model.calls) == 1 + 3


def test_react_loop_handles_unknown_tool() -> None:
    model = ScriptedModel(
        [
            AgentResponse(
                text="",
                tool_calls=[ToolCall(id="c1", name="missing", arguments={})],
            ),
            AgentResponse(text="recovered"),
        ]
    )
    agent = Agent(tools=[add_numbers], knowledge=False)
    _use_model(agent, model)

    out = agent.run("call missing")

    assert out.text == "recovered"
    second = model.calls[1]
    tool_msg = next(m for m in second if m["role"] == "tool")
    assert "not found" in tool_msg["content"]
