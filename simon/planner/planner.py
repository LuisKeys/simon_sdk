import asyncio
import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field

from simon.agent import Agent

PENDING = "pending"
IN_PROGRESS = "in_progress"
DONE = "done"

_ICONS = {PENDING: "○", IN_PROGRESS: "◐", DONE: "✓"}

_PLAN_SYSTEM = (
    "You are a planning assistant. Break the user's goal into a short, ordered "
    "list of concrete tasks. Reply with ONLY a JSON array of strings, e.g. "
    '["first task", "second task"]. No prose, no numbering.'
)


@dataclass
class Task:
    description: str
    status: str = PENDING
    result: str | None = None


def render_tasks(tasks: list[Task]) -> str:
    """Render the task list as a checklist string."""
    return "\n".join(f"{_ICONS[t.status]} {t.description}" for t in tasks)


def _print_tasks(tasks: list[Task]) -> None:
    print("\n" + render_tasks(tasks) + "\n")


def _parse_tasks(text: str) -> list[str]:
    """Extract a list of task strings from the model's reply, robustly."""
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, list):
                return [str(item).strip() for item in data if str(item).strip()]
        except json.JSONDecodeError:
            pass
    # Fallback: treat non-empty lines as tasks.
    lines = [re.sub(r"^[\s\-\*\d\.\)]+", "", ln).strip() for ln in text.splitlines()]
    return [ln for ln in lines if ln]


class Planner:
    """Decompose a goal into tasks, display them, and run each via an Agent."""

    def __init__(
        self,
        agent: Agent | None = None,
        on_update: Callable[[list[Task]], None] | None = None,
    ) -> None:
        self.agent = agent or Agent(knowledge=False)
        self.on_update = on_update or _print_tasks
        self.tasks: list[Task] = []
        # Dedicated agent that only produces the task list.
        self.planner_agent = Agent(
            model=self.agent._model_name,
            knowledge=False,
            system_prompt=_PLAN_SYSTEM,
        )

    def _emit(self) -> None:
        self.on_update(self.tasks)

    async def plan_async(self, goal: str) -> list[Task]:
        response = await self.planner_agent.run_async(goal)
        self.tasks = [Task(description=d) for d in _parse_tasks(response.text)]
        self._emit()
        return self.tasks

    async def run_async(self, goal: str) -> list[Task]:
        await self.plan_async(goal)
        for task in self.tasks:
            task.status = IN_PROGRESS
            self._emit()
            response = await self.agent.run_async(task.description)
            task.result = response.text
            task.status = DONE
            self._emit()
        return self.tasks

    def plan(self, goal: str) -> list[Task]:
        return asyncio.run(self.plan_async(goal))

    def run(self, goal: str) -> list[Task]:
        return asyncio.run(self.run_async(goal))
