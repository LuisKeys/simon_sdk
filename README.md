# Simon SDK

Simon SDK is the simplest way to build AI agents.

**Primary goal:** build a useful AI agent in fewer than 10 lines of Python.

Simon SDK is educational, lightweight, and easy to extend. It favors simplicity over flexibility and developer experience over feature volume.

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Provider Configuration](#provider-configuration)
  - [Knowledge directory flags](#knowledge-directory-flags)
  - [Routing rules](#routing-rules)
- [Quick Start](#quick-start)
- [Examples](#examples)
  - [Basic Agent](#basic-agent)
  - [Memory](#memory)
  - [Knowledge Base](#knowledge-base)
  - [Custom Tools](#custom-tools)
  - [Built-in Tools](#built-in-tools)
  - [Parallel Agents](#parallel-agents)
  - [Triage Agent](#triage-agent)
  - [Chat TUI](#chat-tui)
  - [Persistent Memory](#persistent-memory)
  - [MCP Agent](#mcp-agent)
  - [Structured Output](#structured-output)
  - [Hooks & Usage Tracking](#hooks--usage-tracking)
- [Reliability — Retry and Timeout](#reliability--retry-and-timeout)
- [CLI](#cli)
- [AgentResponse and Token Usage](#agentresponse-and-token-usage)
- [Error Handling](#error-handling)
- [Architecture](#architecture)
- [Running the tests](#running-the-tests)

---

## Requirements

| Requirement | Version |
|---|---|
| Python | ≥ 3.12 |
| Conda (recommended) | any recent version |
| pip | bundled with Conda |

**Python dependencies** (installed automatically):

| Package | Purpose |
|---|---|
| `pydantic` ≥ 2.7 | Settings validation |
| `pydantic-settings` ≥ 2.3 | `.env` loading |
| `openai` ≥ 1.40 | OpenAI provider + web search |
| `anthropic` ≥ 0.34 | Anthropic/Claude provider |
| `ollama` ≥ 0.3 | Local Ollama provider |
| `voyageai` ≥ 0.2 | Anthropic embeddings via Voyage AI (optional) |
| `pypdf` ≥ 4.2 | PDF ingestion for knowledge base |
| `python-docx` ≥ 1.1 | Word document ingestion |
| `openpyxl` ≥ 3.1 | Excel spreadsheet ingestion |
| `python-pptx` ≥ 0.6 | PowerPoint ingestion |
| `numpy` ≥ 1.26 | Embedding storage and similarity search |

**Dev / testing extras** (installed with `[dev]`):

| Package | Purpose |
|---|---|
| `pytest` ≥ 8.2 | Test runner |
| `pytest-asyncio` ≥ 0.23 | Async test support |

**MCP extras** (installed with `[mcp]`):

| Package | Purpose |
|---|---|
| `mcp` ≥ 1.0 | MCP client/server support |

**Optional external services** (at least one is needed for real LLM responses):

- **OpenAI** — set `OPENAI_API_KEY` (cloud, paid)
- **Anthropic** — set `ANTHROPIC_API_KEY` (cloud, paid)
- **Ollama** — run a local Ollama server (`OLLAMA_HOST=http://localhost:11434`) (local, free)

If none of the above is configured, Simon falls back to an **EchoModel** that simply mirrors the prompt back — useful for testing without any API key.

---

## Installation

### Option A — Conda (recommended)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/simon-sdk.git
cd simon-sdk

# 2. Create and activate the Conda environment
conda env create -f environment.yml
conda activate simon

# 3. Install Simon SDK in editable mode (already done by environment.yml,
#    but run this if you skipped step 2 or created the env manually)
pip install -e .
```

### Option B — plain pip (virtualenv)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

### Option C — pip with dev extras (for running tests)

```bash
pip install -e ".[dev]"
```

### Option D — pip with MCP extras

```bash
pip install -e ".[mcp]"
```

---

## Provider Configuration

Copy the example environment file and fill in the keys you want to use:

```bash
cp .env.example .env
```

Edit `.env`:

```dotenv
# --- OpenAI ---
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini          # any OpenAI model name

# --- Anthropic ---
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-latest

# --- Ollama (local, no API key required) ---
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1             # any model you have pulled locally

# --- Routing ---
# AUTO             → Simon picks the best available provider
# OPENAI_MODEL     → force OpenAI
# ANTHROPIC_MODEL  → force Anthropic
# OLLAMA_MODEL     → force Ollama
# (case-insensitive)
DEFAULT_MODEL=AUTO

# --- Embeddings ---
# OPENAI     → text-embedding-3-small / text-embedding-3-large / text-embedding-ada-002
# OLLAMA     → nomic-embed-text:latest / mxbai-embed-large / any model pulled locally
# ANTHROPIC  → voyage-3 / voyage-3-lite / voyage-code-3 (via Voyage AI, requires voyageai package)
EMBEDDING_PROVIDER=OPENAI
EMBEDDING_MODEL=text-embedding-3-small

# --- Knowledge base — folders to auto-index (true/false) ---
ENABLE_DIR_DOCUMENTS=true
ENABLE_DIR_DOWNLOADS=true
ENABLE_DIR_PICTURES=false
ENABLE_DIR_DESKTOP=false

# --- Logging (disabled by default) ---
# SIMON_LOGGING_ENABLED=true
# SIMON_LOG_LEVEL=INFO   # DEBUG | INFO | WARNING
```

### Knowledge directory flags

When `knowledge=True` (the default), Simon auto-indexes the directories enabled in `.env`:

| Flag | Default | Directory |
|---|---|---|
| `ENABLE_DIR_DOCUMENTS` | `true` | `~/Documents` |
| `ENABLE_DIR_DOWNLOADS` | `true` | `~/Downloads` |
| `ENABLE_DIR_PICTURES` | `false` | `~/Pictures` |
| `ENABLE_DIR_DESKTOP` | `false` | `~/Desktop` |

Only directories that both have their flag set to `true` **and** exist on disk are indexed. This works cross-platform (Windows, macOS, Linux).

### Routing rules

When `DEFAULT_MODEL=auto` (the default), Simon selects a provider using these rules:

- **Complex tasks** (prompt contains words like *analyze*, *reasoning*, *multi-step*, …) → prefers online providers (OpenAI → Anthropic → Ollama).
- **Simple tasks** → prefers local first (Ollama → OpenAI → Anthropic).
- A model name passed explicitly to `Agent(model=...)` always overrides the above.
- If no provider is reachable, the `EchoModel` is used (returns the prompt unchanged — good for offline testing).

You can force a specific provider by setting `DEFAULT_MODEL` to one of the semantic labels:

| Value | Provider forced |
|---|---|
| `AUTO` | Smart routing (default) |
| `OPENAI_MODEL` | OpenAI (uses `OPENAI_MODEL`) |
| `ANTHROPIC_MODEL` | Anthropic (uses `ANTHROPIC_MODEL`) |
| `OLLAMA_MODEL` | Ollama (uses `OLLAMA_MODEL`) |

Labels are **case-insensitive** — `ollama_model`, `OLLAMA_MODEL`, and `Ollama_Model` all work. If the forced provider is not configured (missing API key or model name), the router returns an `EchoModel` instead of falling back to another provider.

---

## Quick Start

```python
from simon import Agent

agent = Agent()
response = agent.run("What is reinforcement learning?")
print(response)
```

Run it:

```bash
python examples/basic_agent.py
```

---

## Examples

All examples live in the [`examples/`](examples/) directory. Run any of them with:

```bash
python examples/<filename>.py
```

---

### Basic Agent

**File:** [examples/basic_agent.py](examples/basic_agent.py)

```python
from simon import Agent

agent = Agent()
print(agent.run("What is reinforcement learning?"))
```

- Creates an agent with default settings (knowledge base enabled, no memory, no custom tools).
- The model is selected automatically based on which provider keys are in `.env`.

---

### Memory

**File:** [examples/memory_agent.py](examples/memory_agent.py)

```python
from simon import Agent

agent = Agent(memory=True)
agent.run("My favorite topic is robotics.")
print(agent.run("What did I say my favorite topic is?"))
```

- `memory=True` activates the in-memory conversation history.
- Every turn (user message + assistant response) is appended and sent back on each subsequent call.
- Memory lives for the lifetime of the `Agent` object; it is not persisted to disk.
- For persistence across runs, use [`JSONFileMemory`](#persistent-memory).

---

### Knowledge Base

**File:** [examples/knowledge_agent.py](examples/knowledge_agent.py)

This example loads the *Attention Is All You Need* paper (PDF) and asks the agent to explain Transformer concepts in plain, jargon-free language.

```python
from pathlib import Path
from simon import Agent

PROMPT = """
You are a friendly teacher explaining AI concepts to a curious 15-year-old.
Using only the document you have been given, explain the following topics.
Keep each answer under 3 sentences. Avoid all math and jargon — use simple
real-world analogies wherever possible.

1. What is a Transformer model and what problem does it solve?
2. What does "attention" mean in this context? Give a simple real-world analogy.
3. What do the encoder and decoder do? (one sentence each)
4. What is multi-head attention, in plain English?
5. Why is positional encoding needed and how can we think about it simply?
"""

if __name__ == "__main__":
    paper_path = Path(__file__).parent / "docs" / "attention_paper.pdf"

    agent = Agent()
    chunks = agent.knowledge.add(str(paper_path))
    if chunks:
        print(f"Indexed {chunks} chunks from {paper_path.name}\n")
    else:
        print(f"{paper_path.name} already indexed — skipping.\n")
    # To force re-indexing: agent.knowledge.add(str(paper_path), force=True)
    print(agent.run(PROMPT))
```

- The knowledge base chunks text, generates embeddings, and stores them locally under `.simon_knowledge/`.
- `knowledge.add()` accepts a **file path** or a **directory path**. Supported formats: `.txt`, `.md`, `.pdf`, `.docx`, `.xlsx`, `.pptx`.
- PDF ingestion requires `pypdf >= 4.2` (included in the `pdf` extra: `pip install simon-sdk[pdf]`).
- `knowledge.add()` skips files that are already indexed. Pass `force=True` to delete the existing index entry and re-process: `agent.knowledge.add(path, force=True)`.
- At query time, the top-2 matching chunks are injected as a system context message.
- The embeddings provider is controlled by `EMBEDDING_PROVIDER` and `EMBEDDING_MODEL` in `.env` (see [Provider Configuration](#provider-configuration)).
- Which directories are auto-indexed is controlled per-folder via `.env` flags (see [Provider Configuration](#provider-configuration)). Pass `knowledge=False` to disable indexing entirely.

---

### Custom Tools

**File:** [examples/tools_agent.py](examples/tools_agent.py)

```python
from simon import Agent, tool

@tool
def weather(city: str) -> str:
    """Return weather for a city."""
    return f"Weather for {city}: sunny"

agent = Agent(tools=[weather])
print(agent.run('tool:weather {"city": "Lima"}'))
```

- The `@tool` decorator wraps any Python function and auto-generates a JSON schema from its signature and docstring.
- Call a tool explicitly using the format `tool:<name> <json_args>`. The agent parses this before sending the prompt to the LLM.
- Multiple tools can be registered: `Agent(tools=[weather, calculator, my_api])`.

---

### Autonomous Tools (ReAct)

The `tool:<name> {json}` syntax is an explicit shortcut. With a real provider
(OpenAI or Anthropic) configured, the agent also runs an **autonomous ReAct
loop**: you ask in plain language and the model decides which tools to call,
sees their results, and keeps going until it has an answer.

```python
from simon import Agent
from simon.tools.builtin import fs_list, fs_read

agent = Agent(tools=[fs_list, fs_read], knowledge=False, max_steps=6)

# No tool: prefix — the model chooses to call fs_list / fs_read itself.
print(agent.run("List the files in the current directory and summarize them."))
```

- `max_steps` (default `6`) caps how many tool-calling rounds run before the
  agent must return a final answer — a simple guard against infinite loops.
- Tool errors (unknown tool, bad arguments, exceptions) are fed back to the
  model as text so it can recover instead of crashing the run.
- Providers without tool support (Ollama, the no-key Echo fallback) simply
  skip the loop and answer in one shot.

---

### Planner

**File:** [examples/planner_agent.py](examples/planner_agent.py)

The `Planner` breaks a goal into an ordered task list, prints it as a live
checklist, and runs each task through an `Agent` — updating the status from
pending (○) to in-progress (◐) to done (✓) as it goes.

```python
from simon import Agent, Planner

planner = Planner(agent=Agent(knowledge=False))
tasks = planner.run("Plan a short blog post about why Python is great for beginners")

for task in tasks:
    print(task.status, task.description, "->", task.result)
```

- Pass `on_update=callback` to render the checklist your own way instead of
  printing it.
- From the CLI: `simon plan "research X and summarize it"`.

---

### Built-in Tools

**File:** [examples/builtin_tools_agent.py](examples/builtin_tools_agent.py)

Simon ships with a set of ready-to-use built-in tools:

```python
from simon import Agent
from simon.tools.builtin import (
    datetime_now,
    fs_list,
    fs_read,
    fs_write,
    shell_run,
    web_search,
)

agent = Agent(
    tools=[datetime_now, fs_list, fs_read, fs_write, shell_run, web_search],
    knowledge=False,
)

# Current UTC time
print(agent.run("tool:datetime_now {}"))

# List a directory
print(agent.run('tool:fs_list {"path": "."}'))

# Write and read a file
agent.run('tool:fs_write {"path": "/tmp/hello.txt", "content": "hello simon"}')
print(agent.run('tool:fs_read {"path": "/tmp/hello.txt"}'))

# Run a shell command
print(agent.run('tool:shell_run {"command": "echo hello from shell"}'))

# Search the web (requires OPENAI_API_KEY)
print(agent.run('tool:web_search {"query": "python asyncio tutorial"}'))
```

| Tool | Import | Description |
|---|---|---|
| `datetime_now` | `simon.tools.builtin` | Returns current UTC timestamp (ISO 8601) |
| `fs_read` | `simon.tools.builtin` | Reads a text file |
| `fs_list` | `simon.tools.builtin` | Lists directory contents |
| `fs_write` | `simon.tools.builtin` | Writes (or creates) a file |
| `shell_run` | `simon.tools.builtin` | Runs a shell command (10 s timeout) |
| `web_search` | `simon.tools.builtin` | Web search via OpenAI's search API |
| `http_get` | `simon.tools.builtin` | Fetches a URL and returns the body |

> **Note:** `web_search` requires a valid `OPENAI_API_KEY` and uses OpenAI's built-in web-search tool. `http_get` is a direct HTTP fetch that works without any API key.

---

### Parallel Agents

**File:** [examples/parallel_agents.py](examples/parallel_agents.py)

```python
from simon import Agent, AgentGroup

group = AgentGroup(
    agents={
        "analyst":   Agent(knowledge=False),
        "critic":    Agent(knowledge=False),
        "summarizer": Agent(knowledge=False),
    }
)

results = group.run_all("What are the trade-offs of microservices vs a monolith?")

for name, response in results.items():
    print(f"=== {name.upper()} ===")
    print(response)
```

- `AgentGroup` runs all agents **concurrently** with `asyncio.gather` — total latency equals the slowest agent, not the sum.
- Each agent receives the same prompt and responds independently.
- Returns a `dict[str, str]` mapping agent name → response.
- Use `await group.run_all_async(prompt)` in async contexts.

---

### Triage Agent

**File:** [examples/triage_agent.py](examples/triage_agent.py)

```python
from simon import Agent, TriageAgent

triage = TriageAgent(
    agents={
        "code":    Agent(knowledge=False),
        "math":    Agent(knowledge=False),
        "writing": Agent(knowledge=False),
    },
    descriptions={
        "code":    "Handles programming questions, debugging, and code reviews.",
        "math":    "Solves mathematical problems, equations, and proofs.",
        "writing": "Helps with essays, creative writing, and editing.",
    },
)

response = triage.run("Write a Python function that reverses a linked list.")
print(response)
```

- A lightweight **router agent** inspects the task and selects the best specialist by name.
- The original prompt is then forwarded to that specialist, whose response is returned.
- Agent selection is done via an LLM call — no hard-coded rules or keyword matching.
- `model=` on `TriageAgent` controls which model the router uses; each specialist can use its own model.
- Raises `ValueError` with the list of available agent names if the router returns an unrecognized name.
- Use `await triage.run_async(prompt)` in async contexts.

---

### Chat TUI

**File:** [examples/chat_tui.py](examples/chat_tui.py)

```python
from simon import Agent, chat

agent = Agent(
    name="Luke",
    memory=True,
    system_prompt="You are Luke, an expert chef...",
)

chat(agent=agent)
```

- `chat()` launches a minimal terminal UI built entirely on Python's standard library — no external dependencies.
- Renders a subset of Markdown in the terminal: **bold**, *italic*, `inline code`, fenced code blocks, headers, and bullet lists — all converted to ANSI-styled output.
- Supports multi-line input (Shift+Enter for newlines) and clean single-key shortcuts (`q` or `Ctrl+C` to quit).
- Pass any `Agent` instance: memory, tools, knowledge base, and system prompts all work transparently inside the TUI.

---

### MCP Agent

**File:** [examples/mcp_agent.py](examples/mcp_agent.py)

`MCPClient` connects to any MCP server via stdio, lists its tools, and returns them as standard Simon `Tool` objects — ready to pass directly to `Agent(tools=[...])`.

```python
from simon import Agent, MCPClient

# Point to any MCP server command
client = MCPClient(["python", "simon/tools/builtin/mcp_example_server.py"])
tools = client.get_tools()

print(f"Tools loaded from MCP server: {[t.name for t in tools]}")

agent = Agent(tools=tools)
response = agent.run("Use the add_numbers tool to compute 37 + 5, then reverse the result string.")
print(response.text)
```

Simon ships a minimal example server in `simon/tools/builtin/mcp_example_server.py` with two tools for local testing:

| Tool | Description |
|---|---|
| `add_numbers(a, b)` | Returns `a + b` |
| `reverse_string(text)` | Reverses the characters in `text` |

**Requirements:** install the `[mcp]` extra before using `MCPClient`:

```bash
pip install -e ".[mcp]"
```

- `MCPClient(command)` accepts any list of strings — the same format as Python's `subprocess` (e.g. `["npx", "-y", "@my/mcp-server"]`).
- Each tool call opens a fresh stdio connection to the server, so the server does not need to stay running between calls.
- `get_tools()` is synchronous; `get_tools_async()` is available for async contexts.

---

### Structured Output

**File:** [examples/structured_output_agent.py](examples/structured_output_agent.py)

Ask the agent to return data as a validated Pydantic model instead of free text.

```python
from pydantic import BaseModel
from simon import Agent

class Recipe(BaseModel):
    title: str
    ingredients: list[str]
    steps: list[str]
    prep_time_minutes: int

agent = Agent(knowledge=False)
response = agent.run("Give me a simple pancake recipe", output_model=Recipe)

recipe: Recipe = response.parsed
print(recipe.title)
print(recipe.prep_time_minutes)
```

- Pass any Pydantic model class as `output_model=` to `agent.run()`.
- The JSON schema is injected as a system message; the model is instructed to return only the raw JSON object.
- Common LLM decorations (` ```json ``` ` fences, leading prose) are stripped automatically before validation.
- If the output is invalid, Simon re-prompts up to `SIMON_STRUCTURED_RETRIES` times (default `2`) with the validation error, giving the model a chance to self-correct.
- If all retries are exhausted a `StructuredOutputError` is raised — catch it to inspect `.raw_text` and `.attempts`.
- `response.text` and all other `AgentResponse` fields are still set normally.

```python
from simon import StructuredOutputError

try:
    response = agent.run("...", output_model=MyModel)
except StructuredOutputError as e:
    print(f"Failed after {e.attempts} attempts. Raw output: {e.raw_text}")
```

---

### Hooks & Usage Tracking

**File:** [examples/hooks_agent.py](examples/hooks_agent.py)

Observe what happens inside each agent run without changing how the agent works.

```python
from simon import Agent, AgentEvent

def on_event(event: AgentEvent) -> None:
    if event.type == "model_selected":
        print(f"Provider: {event.data['model']}")
    elif event.type == "tool_called":
        print(f"Tool: {event.data['tool']} → {event.data['result'][:60]}")
    elif event.type == "response_received":
        print(f"Done in {event.data['latency']:.2f}s")

agent = Agent(knowledge=False, on_event=on_event)
agent.run("What is 2 + 2?")

# Accumulated token usage across all runs
print(agent.total_usage)   # Usage(input_tokens=..., output_tokens=..., total_tokens=...)
```

**Event types:**

| `event.type` | `event.data` keys | When |
|---|---|---|
| `model_selected` | `model`, `model_id` | Provider resolved, before first LLM call |
| `tool_called` | `tool`, `arguments`, `result` (truncated to 200 chars) | After each tool executes in the ReAct loop |
| `retry_attempted` | `attempt`, `error` | Before each retry sleep in `with_retry` |
| `response_received` | `latency`, `usage`, `steps` | Final response ready |

- `Agent.total_usage` — a `Usage` dataclass that accumulates tokens across **all** `run()` calls on this agent instance, including intermediate ReAct tool-loop calls. Multiply by your provider's per-token rate to compute cost.
- A buggy `on_event` callback never crashes the run — exceptions are swallowed and logged at `WARNING` level.

---

### Persistent Memory

**File:** [examples/persistent_memory_agent.py](examples/persistent_memory_agent.py)

```python
from simon import Agent, JSONFileMemory

memory = JSONFileMemory("robotics_chat.json")
agent = Agent(memory=memory)

print(agent.run("What did I say my favorite topic is?"))
agent.run("My favorite topic is robotics.")
```

- `JSONFileMemory` stores the full conversation in a human-readable JSON file under `.simon_chats/`.
- Just pass a **filename** — the directory is always `.simon_chats/` regardless of what you type.
- Run the script twice: the second run picks up exactly where the first left off.
- The file is a plain JSON list of `{"role", "content"}` objects — open it in any editor, version it with git (add `.simon_chats/` to `.gitignore` to keep it local), or delete it to start fresh.
- `memory=` on `Agent` accepts `True` (in-memory), `False` (disabled), or any `BaseMemory` instance:

```python
# In-memory (default, not persisted)
agent = Agent(memory=True)

# Persistent, named conversation
agent = Agent(memory=JSONFileMemory("support.json"))
```

---

### Reliability — Retry and Timeout

Simon automatically retries transient model failures (rate limits, 5xx errors, timeouts) with exponential backoff. This is enabled by default and requires no code changes.

Configure it via `.env`:

```dotenv
SIMON_MAX_RETRIES=2         # extra attempts after the first try (default: 2)
SIMON_REQUEST_TIMEOUT=60    # seconds per attempt (default: 60)
SIMON_RETRY_BASE_DELAY=0.5  # seconds; doubles each retry (default: 0.5)
```

Set `SIMON_MAX_RETRIES=0` to disable retries entirely.

---

### CLI

Simon ships with a command-line interface. After installation (`pip install -e .`), the `simon` command is available:

```bash
# Start an interactive terminal chat
simon chat

# Ask a single question and print the answer
simon ask "What is gradient descent?"

# Index a file or folder into the knowledge base
simon index ./docs/

# Decompose a goal into tasks and run them as a live checklist
simon plan "research the pros and cons of microservices and summarize them"

# Force a specific provider for any command
simon --model OPENAI_MODEL ask "Summarize this in one sentence."
```

| Command | Description |
|---|---|
| `simon chat` | Launches the interactive terminal UI |
| `simon ask "<prompt>"` | Single prompt, prints response, exits |
| `simon index <path>` | Indexes a file or directory into the knowledge base |
| `simon plan "<goal>"` | Breaks a goal into tasks and runs each as a checklist |

---

## AgentResponse and Token Usage

`agent.run()` returns an `AgentResponse` object.

```python
from simon import Agent

agent = Agent()
response = agent.run("Explain gradient descent in one sentence.")

print(response)              # __str__ returns .text — existing code unchanged
print(response.text)         # the assistant's reply
print(response.usage)        # Usage(input_tokens=..., output_tokens=..., total_tokens=...)
print(response.parsed)       # validated Pydantic instance when output_model= was used
```

| Field | Type | Description |
|---|---|---|
| `text` | `str` | The assistant's reply |
| `usage` | `Usage \| None` | Token counts; `None` for Ollama and Echo |
| `tool_calls` | `list[ToolCall]` | Tool invocations requested by the model |
| `stop_reason` | `str \| None` | Provider stop reason (`"stop"`, `"tool_calls"`, …) |
| `parsed` | `Any \| None` | Validated Pydantic instance when `output_model=` was used |

`agent.total_usage` accumulates `Usage` across every `run()` call on that agent instance (including ReAct intermediate calls). Use it to track spend:

```python
# Cost estimate example (OpenAI gpt-4o-mini rates as of 2025)
cost = agent.total_usage.input_tokens * 0.00000015 + agent.total_usage.output_tokens * 0.00000060
print(f"Estimated cost: ${cost:.6f}")
```

Structured logging is opt-in via `.env`. Set `SIMON_LOGGING_ENABLED=true` and optionally `SIMON_LOG_LEVEL=DEBUG` (or `INFO` / `WARNING`). Each `run()` call logs model name, latency, and token counts at the chosen level.

---

## Error Handling

Simon raises its own exception hierarchy — all subclasses of `SimonError` — so you can catch everything Simon raises with a single `except SimonError` clause, or target specific categories:

```python
from simon import SimonError, ProviderError, ToolError, KnowledgeError, StructuredOutputError

try:
    response = agent.run("...", output_model=MyModel)
except StructuredOutputError as e:
    # Model never produced valid JSON after all retries
    print(f"Raw output: {e.raw_text} ({e.attempts} attempts)")
except ProviderError:
    # Provider package not installed, or API unreachable
    ...
except KnowledgeError:
    # Knowledge base ingestion problem (missing package, bad path, …)
    ...
except ToolError:
    # Malformed tool call arguments
    ...
except SimonError:
    # Catch-all for any other Simon error
    ...
```

All Simon exceptions use **dual inheritance** — `ProviderError` is both a `SimonError` and a `RuntimeError`, `ToolError` is both a `SimonError` and a `ValueError` — so existing code that catches `RuntimeError` or `ValueError` continues to work without changes.

Simon is also PEP 561-compliant: a `py.typed` marker is included so type checkers (mypy, pyright) pick up its inline type annotations automatically.

---

## Architecture

```
simon/
├── agent/
│   ├── agent.py      # Agent — single-agent entry point
│   ├── events.py     # AgentEvent dataclass (hooks system)
│   ├── response.py   # AgentResponse + Usage dataclasses
│   └── structured.py # schema_instruction + parse_structured (structured output)
├── cli.py            # `simon` CLI entry point (chat / ask / index / plan)
├── config/           # Settings loaded from .env via pydantic-settings
├── exceptions.py     # SimonError hierarchy (ProviderError, ToolError, KnowledgeError, StructuredOutputError)
├── knowledge/        # Chunking, embedding, and retrieval (numpy-backed)
├── memory/           # BaseMemory, InMemoryMemory, JSONFileMemory
├── models/           # Provider wrappers: OpenAI, Anthropic, Ollama, Echo
├── multi/            # Multi-agent: AgentGroup (parallel) + TriageAgent (router)
├── py.typed          # PEP 561 marker — enables inline type checking
├── reliability.py    # with_retry — exponential backoff + per-attempt timeout
├── router/           # ModelRouter — provider selection logic
├── tui.py            # Terminal chat UI with Markdown rendering (stdlib only)
└── tools/
    ├── tool.py        # @tool decorator + ToolRegistry
    ├── mcp_client.py  # MCPClient — connect to any MCP server and load its tools
    └── builtin/       # datetime_now, fs_*, shell_run, web_search, http_get + mcp_example_server
```

### Core concepts

1. **`Agent`** — the single-agent entry point. Wires memory, knowledge, tools, and a model together. Accepts `on_event=` for observability and exposes `total_usage` for cumulative token tracking.
2. **`AgentGroup`** — runs multiple `Agent` instances in parallel over the same prompt using `asyncio.gather`. Returns `dict[str, str]`.
3. **`TriageAgent`** — a router agent that selects the right specialist for a task via an LLM call, then delegates the original prompt to that specialist.
4. **`Memory`** — pluggable conversation history. `InMemoryMemory` (default, in-process list) or `JSONFileMemory` (persisted to `.simon_chats/<name>.json`). Implement `BaseMemory` to add your own backend.
5. **`KnowledgeBase`** — ingest documents, chunk them, embed with the provider set via `EMBEDDING_PROVIDER` / `EMBEDDING_MODEL`, and retrieve by cosine similarity at query time. Index files are stored in `.simon_knowledge/`.
6. **`@tool`** — a decorator that turns any typed Python function into a callable tool with an auto-generated JSON schema.
7. **`MCPClient`** — connects to an external MCP server via stdio, lists its tools, and wraps each as a `Tool` compatible with `Agent(tools=[...])`. Requires `pip install -e ".[mcp]"`.
8. **`ModelRouter`** — selects the right provider at runtime based on available API keys, the `DEFAULT_MODEL` env var, and a simple task-complexity heuristic.
9. **`structured output`** — pass `output_model=MyPydanticModel` to `agent.run()` to get a validated instance back in `response.parsed`. Works with all providers via prompt injection + parse + auto-correction loop.
10. **`SimonError` hierarchy** — `ProviderError`, `ToolError`, `KnowledgeError`, `StructuredOutputError` with dual inheritance so existing `except RuntimeError` / `except ValueError` callers are unaffected.

### Async support

Every public `run()` method is a synchronous convenience wrapper around its `run_async()` counterpart. In async contexts (e.g., FastAPI, Jupyter with a running event loop), call the async variant directly:

```python
response  = await agent.run_async(prompt)
results   = await group.run_all_async(prompt)
response  = await triage.run_async(prompt)
```

---


## Running the tests

```bash
# activate your environment first
conda activate simon   # or: source .venv/bin/activate

pytest
```

Tests live in `tests/`. They use `pytest-asyncio` for async test cases.

---

## Non-goals

The following are intentionally out of scope:

- Workflow engines and event buses
- Distributed execution
- Full MCP server hosting (only client-side consumption is supported)
- Docker / Kubernetes requirements
- Enterprise features (auth, RBAC, audit logs, …)
