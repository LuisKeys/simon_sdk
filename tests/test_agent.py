from simon import Agent


def test_agent_creation(monkeypatch) -> None:
    monkeypatch.setattr("simon.router.router.settings.openai_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.openai_model", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_model", "")
    monkeypatch.setattr("simon.router.router.settings.ollama_model", "")
    monkeypatch.delenv("OLLAMA_HOST", raising=False)

    agent = Agent()
    assert agent is not None


def test_agent_run_returns_text(monkeypatch) -> None:
    monkeypatch.setattr("simon.router.router.settings.openai_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.openai_model", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_model", "")
    monkeypatch.setattr("simon.router.router.settings.ollama_model", "")
    monkeypatch.delenv("OLLAMA_HOST", raising=False)

    agent = Agent()
    out = agent.run("hello")
    assert isinstance(out, str)
    assert "hello" in out.lower()
