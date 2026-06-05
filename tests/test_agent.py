from simon import Agent
from simon.agent.response import AgentResponse


def test_agent_creation(monkeypatch) -> None:
    monkeypatch.setattr("simon.router.router.settings.openai_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.openai_model", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_model", "")
    monkeypatch.setattr("simon.router.router.settings.ollama_model", "")
    monkeypatch.delenv("OLLAMA_HOST", raising=False)

    agent = Agent()
    assert agent is not None


def test_agent_run_returns_agent_response(monkeypatch) -> None:
    monkeypatch.setattr("simon.router.router.settings.openai_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.openai_model", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_model", "")
    monkeypatch.setattr("simon.router.router.settings.ollama_model", "")
    monkeypatch.delenv("OLLAMA_HOST", raising=False)

    agent = Agent(knowledge=False)
    out = agent.run("hello")
    assert isinstance(out, AgentResponse)
    assert "hello" in out.text.lower()
    assert str(out) == out.text  # backwards-compat via __str__
    assert out.usage is None  # EchoModel has no usage
