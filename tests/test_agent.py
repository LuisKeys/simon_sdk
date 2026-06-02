from simon import Agent


def test_agent_creation() -> None:
    agent = Agent()
    assert agent is not None


def test_agent_run_returns_text() -> None:
    agent = Agent()
    out = agent.run("hello")
    assert isinstance(out, str)
    assert "hello" in out.lower()
