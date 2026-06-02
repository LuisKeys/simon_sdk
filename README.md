# Simon SDK

Simon SDK is the simplest way to build AI agents.

Primary goal: build a useful AI agent in less than 10 lines of code.

Simon SDK is educational, lightweight, and easy to extend. It favors simplicity over flexibility and developer experience over feature volume.

## Installation

Conda-first setup:

```bash
conda env create -f environment.yml
conda activate simon
pip install -e .
```

## Quick Start

```python
from simon import Agent

agent = Agent()
response = agent.run("What is reinforcement learning?")
print(response)
```

## Tools Example

```python
from simon import Agent, tool

@tool
def weather(city: str) -> str:
    """Return weather for a city."""
    return f"Sunny in {city}"

agent = Agent(tools=[weather])
print(agent.run('tool:weather {"city": "Quito"}'))
```

## Memory Example

```python
from simon import Agent

agent = Agent(memory=True)
agent.run("My name is Ana")
print(agent.run("What did I just tell you?"))
```

## Knowledge Example

```python
from simon import Agent

agent = Agent()
agent.knowledge.add("docs/")
print(agent.run("Summarize the docs"))
```

## Provider Configuration

Copy [.env.example](.env.example) to `.env` and set keys as needed.

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `OLLAMA_HOST`
- `DEFAULT_MODEL`

Routing defaults:

- If model starts with `gpt` -> OpenAI
- If model starts with `claude` -> Anthropic
- If model starts with `ollama` or `llama` -> Ollama
- If no provider is configured -> local echo fallback for a zero-config start

## Architecture

Core concepts in v1:

1. `Agent` as the only required entry point.
2. Optional `Memory` with a simple abstraction and in-memory implementation.
3. `Knowledge` ingestion, chunking, embeddings, and retrieval.
4. Decorator-based `Tools` with automatic JSON schema generation.
5. Provider-agnostic `Models` with lightweight routing.

## Non-goals (v1)

Not included in v1:

- Multi-agent systems
- Agent orchestration and graphs
- Workflow engines and event buses
- Distributed execution
- MCP integration
- Docker/Kubernetes requirements
- GUI/TUI layers
- Enterprise features
