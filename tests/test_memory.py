from simon import Agent


def test_memory_enabled() -> None:
    agent = Agent(memory=True)
    agent.run("hello memory")
    history = agent.run("tool:missing {}")
    assert isinstance(history, str)


def test_memory_disabled() -> None:
    agent = Agent(memory=False)
    out = agent.run("hello")
    assert "hello" in out.lower()
