import pytest
from pydantic import BaseModel as PydanticBaseModel

from simon import Agent
from simon.agent.response import AgentResponse, Usage
from simon.agent.structured import parse_structured, schema_instruction
from simon.exceptions import StructuredOutputError
from simon.models.base import BaseModel


class Person(PydanticBaseModel):
    name: str
    age: int


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


def _force_echo(monkeypatch) -> None:
    monkeypatch.setattr("simon.router.router.settings.openai_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.openai_model", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_model", "")
    monkeypatch.setattr("simon.router.router.settings.ollama_model", "")
    monkeypatch.delenv("OLLAMA_HOST", raising=False)


# --- Unit tests for parse_structured ---

def test_parse_structured_happy_path():
    result = parse_structured('{"name": "Ada", "age": 36}', Person)
    assert result.name == "Ada"
    assert result.age == 36


def test_parse_structured_strips_fences():
    text = '```json\n{"name": "Ada", "age": 36}\n```'
    result = parse_structured(text, Person)
    assert result.name == "Ada"


def test_parse_structured_strips_prose():
    text = 'Here is the JSON: {"name": "Ada", "age": 36} done'
    result = parse_structured(text, Person)
    assert result.name == "Ada"


def test_parse_structured_raises_on_invalid():
    with pytest.raises(Exception):
        parse_structured('{"name": "Ada", "age": "not-a-number"}', Person)


def test_schema_instruction_contains_schema():
    instruction = schema_instruction(Person)
    assert "name" in instruction
    assert "age" in instruction
    assert "JSON" in instruction


# --- Integration tests via Agent ---

def test_output_model_happy_path():
    model = ScriptedModel([AgentResponse(text='{"name": "Ada", "age": 36}')])
    agent = Agent(knowledge=False)
    _use_model(agent, model)

    out = agent.run("describe a person", output_model=Person)
    assert isinstance(out.parsed, Person)
    assert out.parsed.name == "Ada"
    assert out.parsed.age == 36
    assert out.text == '{"name": "Ada", "age": 36}'


def test_output_model_fenced_response():
    model = ScriptedModel([AgentResponse(text='```json\n{"name": "Ada", "age": 36}\n```')])
    agent = Agent(knowledge=False)
    _use_model(agent, model)

    out = agent.run("describe a person", output_model=Person)
    assert isinstance(out.parsed, Person)


def test_output_model_self_correction():
    model = ScriptedModel([
        AgentResponse(text='{"name": "Ada", "age": "old"}'),  # invalid
        AgentResponse(text='{"name": "Ada", "age": 36}'),      # valid
    ])
    agent = Agent(knowledge=False)
    _use_model(agent, model)

    out = agent.run("describe a person", output_model=Person)
    assert isinstance(out.parsed, Person)
    assert len(model.calls) == 2
    # Second call should contain a correction user message
    second_messages = model.calls[1]
    assert any(
        m["role"] == "user" and "corrected JSON" in m["content"]
        for m in second_messages
    )


def test_output_model_exhaustion_raises():
    model = ScriptedModel([AgentResponse(text="not json at all")] * 10)
    agent = Agent(knowledge=False)
    _use_model(agent, model)

    with pytest.raises(StructuredOutputError) as exc_info:
        agent.run("describe a person", output_model=Person)

    assert exc_info.value.raw_text == "not json at all"
    assert exc_info.value.attempts > 0


def test_output_model_echo_raises(monkeypatch):
    _force_echo(monkeypatch)
    agent = Agent(knowledge=False)

    with pytest.raises(StructuredOutputError):
        agent.run("describe a person", output_model=Person)


def test_no_output_model_returns_none_parsed():
    model = ScriptedModel([AgentResponse(text="hello")])
    agent = Agent(knowledge=False)
    _use_model(agent, model)

    out = agent.run("say hello")
    assert out.parsed is None
