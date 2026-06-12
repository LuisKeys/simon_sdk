import pytest

from simon.exceptions import (
    KnowledgeError,
    ProviderError,
    SimonError,
    StructuredOutputError,
    ToolError,
)
from simon.tools.tool import tool


@tool
def dummy_tool(x: int) -> int:
    """A dummy tool for testing."""
    return x


def _force_echo(monkeypatch) -> None:
    monkeypatch.setattr("simon.router.router.settings.openai_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.openai_model", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_model", "")
    monkeypatch.setattr("simon.router.router.settings.ollama_model", "")
    monkeypatch.delenv("OLLAMA_HOST", raising=False)


def test_hierarchy():
    assert issubclass(ProviderError, (SimonError, RuntimeError))
    assert issubclass(ToolError, (SimonError, ValueError))
    assert issubclass(KnowledgeError, (SimonError, RuntimeError))
    assert issubclass(StructuredOutputError, SimonError)


def test_structured_output_error_attributes():
    exc = StructuredOutputError("bad", raw_text="oops", attempts=3)
    assert exc.raw_text == "oops"
    assert exc.attempts == 3
    assert str(exc) == "bad"


def test_knowledge_error_is_runtime_error(monkeypatch):
    """KnowledgeError must still be catchable as RuntimeError for backward compat."""
    _force_echo(monkeypatch)
    from simon import Agent

    agent = Agent(knowledge=False)
    with pytest.raises(RuntimeError):
        agent.add_knowledge("/some/path")


def test_knowledge_error_is_simon_error(monkeypatch):
    _force_echo(monkeypatch)
    from simon import Agent

    agent = Agent(knowledge=False)
    with pytest.raises(SimonError):
        agent.add_knowledge("/some/path")


def test_tool_error_is_value_error(monkeypatch):
    """ToolError must still be catchable as ValueError for backward compat."""
    _force_echo(monkeypatch)
    from simon import Agent

    # Register a tool; pass valid JSON that is not a dict (a list) to trigger ToolError
    agent = Agent(tools=[dummy_tool], knowledge=False)
    with pytest.raises(ValueError):
        agent.run('tool:dummy_tool [1, 2]')


def test_tool_error_is_simon_error(monkeypatch):
    _force_echo(monkeypatch)
    from simon import Agent

    agent = Agent(tools=[dummy_tool], knowledge=False)
    with pytest.raises(SimonError):
        agent.run('tool:dummy_tool [1, 2]')
