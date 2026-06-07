from simon import Agent, JSONFileMemory
from simon.agent.response import AgentResponse


def _force_echo(monkeypatch) -> None:
    monkeypatch.setattr("simon.router.router.settings.openai_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.openai_model", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_model", "")
    monkeypatch.setattr("simon.router.router.settings.ollama_model", "")
    monkeypatch.delenv("OLLAMA_HOST", raising=False)


def test_accepts_custom_memory_instance(monkeypatch, tmp_path) -> None:
    _force_echo(monkeypatch)
    monkeypatch.setattr("simon.memory.jsonfile._CHATS_DIR", tmp_path / ".simon_chats")

    mem = JSONFileMemory("conv.json")
    agent = Agent(memory=mem, knowledge=False)
    assert agent.memory is mem

    agent.run("hello there")
    # The custom memory recorded both user and assistant turns and persisted.
    assert (tmp_path / ".simon_chats" / "conv.json").exists()


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
