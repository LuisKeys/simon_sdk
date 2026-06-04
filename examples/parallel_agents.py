"""Example: run three specialized agents in parallel over the same prompt."""

from simon import Agent, AgentGroup

analyst = Agent(knowledge=False, memory=False)
critic = Agent(knowledge=False, memory=False)
summarizer = Agent(knowledge=False, memory=False)

group = AgentGroup(
    agents={
        "analyst": analyst,
        "critic": critic,
        "summarizer": summarizer,
    }
)

prompt = "What are the main trade-offs of microservices vs a monolith?"

results = group.run_all(prompt)

for name, response in results.items():
    print(f"=== {name.upper()} ===")
    print(response)
    print()
