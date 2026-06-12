"""Example: observability hooks and usage tracking.

Run:
    python examples/hooks_agent.py
"""

from simon import Agent, AgentEvent


def on_event(event: AgentEvent) -> None:
    if event.type == "model_selected":
        print(f"[{event.type}] provider={event.data.get('model')}")
    elif event.type == "tool_called":
        print(f"[{event.type}] {event.data.get('tool')} → {event.data.get('result', '')[:60]}")
    elif event.type == "retry_attempted":
        print(f"[{event.type}] attempt={event.data.get('attempt')} error={event.data.get('error')}")
    elif event.type == "response_received":
        print(f"[{event.type}] latency={event.data.get('latency', 0):.2f}s")


agent = Agent(knowledge=False, on_event=on_event)

response = agent.run("What is 2 + 2?")
print(f"\nResponse: {response.text}")
print(f"Total usage: {agent.total_usage}")
