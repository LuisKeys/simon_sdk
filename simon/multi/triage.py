import asyncio

from simon.agent import Agent


class TriageAgent:
    """Router agent that delegates a task to the best-fit specialist agent.

    The router uses an internal LLM call to select an agent by name, then
    forwards the original prompt to that agent and returns its response.
    """

    def __init__(
        self,
        agents: dict[str, Agent],
        descriptions: dict[str, str],
        model: str | None = None,
    ) -> None:
        if not agents:
            raise ValueError("agents dict must not be empty.")
        missing = [n for n in agents if n not in descriptions]
        if missing:
            raise ValueError(f"Missing descriptions for agents: {missing}")
        self.agents = agents
        self.descriptions = descriptions
        self._router_agent = Agent(model=model, memory=False, tools=None, knowledge=False)

    def _routing_prompt(self, task: str) -> str:
        lines = [
            "You are a task router. Given the task below, reply with ONLY the name of",
            "the most suitable agent from the list. No punctuation, no explanation.",
            "",
            "Available agents:",
        ]
        for name, desc in self.descriptions.items():
            lines.append(f"  {name}: {desc}")
        lines += ["", f"Task: {task}", "", "Agent name:"]
        return "\n".join(lines)

    async def run_async(self, prompt: str) -> str:
        routing_prompt = self._routing_prompt(prompt)
        chosen = (await self._router_agent.run_async(routing_prompt)).strip()

        # Tolerate minor LLM formatting (trailing punctuation, mixed case)
        chosen_clean = chosen.strip(".,;:!? \t\n")
        match = next(
            (n for n in self.agents if n.lower() == chosen_clean.lower()), None
        )
        if match is None:
            available = ", ".join(self.agents.keys())
            raise ValueError(
                f"Router returned unknown agent '{chosen}'. Available: {available}"
            )

        return await self.agents[match].run_async(prompt)

    def run(self, prompt: str) -> str:
        try:
            asyncio.get_running_loop()
            raise RuntimeError(
                "An event loop is already running. Use `await triage.run_async(...)`."
            )
        except RuntimeError as exc:
            if "already running" in str(exc):
                raise
        return asyncio.run(self.run_async(prompt))
