import asyncio

from simon.agent import Agent


class AgentGroup:
    """Run multiple agents in parallel over the same prompt."""

    def __init__(self, agents: dict[str, Agent]) -> None:
        self.agents = agents

    async def run_all_async(self, prompt: str) -> dict[str, str]:
        names = list(self.agents.keys())
        responses = await asyncio.gather(
            *[self.agents[n].run_async(prompt) for n in names]
        )
        return dict(zip(names, responses))

    def run_all(self, prompt: str) -> dict[str, str]:
        try:
            asyncio.get_running_loop()
            raise RuntimeError(
                "An event loop is already running. Use `await group.run_all_async(...)`."
            )
        except RuntimeError as exc:
            if "already running" in str(exc):
                raise
        return asyncio.run(self.run_all_async(prompt))
