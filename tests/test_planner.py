from simon import Agent, Planner
from simon.agent.response import AgentResponse
from simon.models.base import BaseModel
from simon.planner import DONE, IN_PROGRESS, PENDING


class CannedModel(BaseModel):
    """Returns a plan JSON first, then a generic answer for each task."""

    def __init__(self) -> None:
        self.first = True

    async def complete(self, messages, tools=None) -> AgentResponse:
        if self.first:
            self.first = False
            return AgentResponse(text='["task one", "task two"]')
        return AgentResponse(text="answer")


def _patch(planner: Planner, model: BaseModel) -> None:
    planner.agent._router.resolve = lambda *a, **k: model  # type: ignore[assignment]
    planner.planner_agent._router.resolve = lambda *a, **k: model  # type: ignore[assignment]


def test_plan_creates_tasks() -> None:
    model = CannedModel()
    planner = Planner(agent=Agent(knowledge=False), on_update=lambda t: None)
    _patch(planner, model)

    tasks = planner.plan("do something")

    assert [t.description for t in tasks] == ["task one", "task two"]
    assert all(t.status == PENDING for t in tasks)


def test_run_transitions_and_emits() -> None:
    model = CannedModel()
    seen_statuses: list[list[str]] = []
    planner = Planner(
        agent=Agent(knowledge=False),
        on_update=lambda tasks: seen_statuses.append([t.status for t in tasks]),
    )
    _patch(planner, model)

    tasks = planner.run("do something")

    assert all(t.status == DONE for t in tasks)
    assert all(t.result == "answer" for t in tasks)
    # An in-progress snapshot was emitted at some point during the run.
    assert any(IN_PROGRESS in snap for snap in seen_statuses)
