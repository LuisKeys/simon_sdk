import pytest
from simon import Agent, AgentGroup, TriageAgent
from simon.agent.response import AgentResponse


def _no_provider(monkeypatch):
    monkeypatch.setattr("simon.router.router.settings.openai_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.openai_model", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_model", "")
    monkeypatch.setattr("simon.router.router.settings.ollama_model", "")
    monkeypatch.delenv("OLLAMA_HOST", raising=False)


# ---------------------------------------------------------------------------
# AgentGroup
# ---------------------------------------------------------------------------

def test_agent_group_run_all_returns_all_names(monkeypatch):
    _no_provider(monkeypatch)
    agents = {
        "a": Agent(knowledge=False),
        "b": Agent(knowledge=False),
        "c": Agent(knowledge=False),
    }
    group = AgentGroup(agents)
    results = group.run_all("ping")
    assert set(results.keys()) == {"a", "b", "c"}
    for v in results.values():
        assert isinstance(v, AgentResponse)
        assert len(v.text) > 0


def test_agent_group_empty_prompt(monkeypatch):
    _no_provider(monkeypatch)
    group = AgentGroup({"x": Agent(knowledge=False)})
    results = group.run_all("")
    assert "x" in results


# ---------------------------------------------------------------------------
# TriageAgent
# ---------------------------------------------------------------------------

def test_triage_raises_on_missing_description():
    agents = {"a": Agent(knowledge=False), "b": Agent(knowledge=False)}
    with pytest.raises(ValueError, match="Missing descriptions"):
        TriageAgent(agents=agents, descriptions={"a": "only a"})


def test_triage_raises_on_empty_agents():
    with pytest.raises(ValueError, match="must not be empty"):
        TriageAgent(agents={}, descriptions={})


def test_triage_run_returns_string(monkeypatch):
    _no_provider(monkeypatch)
    # EchoModel echoes the prompt back; the router will echo the routing prompt.
    # We patch run_async on the internal router agent so it always returns a
    # valid agent name, then verify the chosen agent's response is returned.
    import simon.multi.triage as triage_module

    agents = {
        "code": Agent(knowledge=False),
        "math": Agent(knowledge=False),
    }
    descriptions = {
        "code": "Programming questions.",
        "math": "Math problems.",
    }
    triage = TriageAgent(agents=agents, descriptions=descriptions)

    # Force the router to always pick "math"
    async def fake_route(_prompt):
        return AgentResponse(text="math")

    triage._router_agent.run_async = fake_route

    result = triage.run("What is 2 + 2?")
    assert isinstance(result, AgentResponse)
    assert len(result.text) > 0


def test_triage_unknown_agent_raises(monkeypatch):
    _no_provider(monkeypatch)
    import simon.multi.triage as triage_module

    agents = {"code": Agent(knowledge=False)}
    descriptions = {"code": "Programming."}
    triage = TriageAgent(agents=agents, descriptions=descriptions)

    async def fake_route(_prompt):
        return AgentResponse(text="nonexistent")

    triage._router_agent.run_async = fake_route

    with pytest.raises(ValueError, match="unknown agent"):
        triage.run("hello")
