# Simon SDK

Simon SDK is the simplest way to build AI agents.

**Primary goal:** build a useful AI agent in fewer than 10 lines of Python.

Simon SDK is educational, lightweight, and easy to extend. It favors simplicity over flexibility and developer experience over feature volume.

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Provider Configuration](#provider-configuration)
- [Quick Start](#quick-start)
- [Examples](#examples)
  - [Basic Agent](#basic-agent)
  - [Memory](#memory)
  - [Knowledge Base](#knowledge-base)
  - [Custom Tools](#custom-tools)
  - [Built-in Tools](#built-in-tools)
- [Architecture](#architecture)
- [Non-goals (v1)](#non-goals-v1)

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
# "auto"             → Simon picks the best available provider
# "gpt-..."          → force OpenAI
# "claude-..."       → force Anthropic
# "ollama" / "llama" → force Ollama
DEFAULT_MODEL=auto
```

### Routing rules

When `DEFAULT_MODEL=auto` (the default), Simon selects a provider using these rules:

- **Complex tasks** (prompt contains words like *analyze*, *reasoning*, *multi-step*, …) → prefers online providers (OpenAI → Anthropic → Ollama).
- **Simple tasks** → prefers local first (Ollama → OpenAI → Anthropic).
- A model name passed explicitly to `Agent(model=...)` always overrides the above.
- If no provider is reachable, the `EchoModel` is used (returns the prompt unchanged — good for offline testing).

You can also force a specific provider by setting `DEFAULT_MODEL` to a concrete model name, e.g. `DEFAULT_MODEL=gpt-4o-mini`.

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

---

### Knowledge Base

**File:** [examples/knowledge_agent.py](examples/knowledge_agent.py)

```python
from pathlib import Path
from simon import Agent

# Create a small demo document
tmp_file = Path("knowledge_demo.txt")
tmp_file.write_text(
    "Reinforcement learning is about agents maximizing reward through interaction.",
    encoding="utf-8",
)

agent = Agent()
agent.knowledge.add(str(tmp_file))   # index a file (or pass a directory path)
print(agent.run("What is reinforcement learning about?"))
```

- The knowledge base chunks text, generates embeddings, and stores them locally under `.simon_knowledge/`.
- `knowledge.add()` accepts a **file path** or a **directory path**. Supported formats: `.txt`, `.md`, `.pdf`, `.docx`, `.xlsx`, `.pptx`.
- At query time, the top-2 matching chunks are injected as a system context message.
- By default, `Agent()` automatically indexes `~/Documents` and `~/Downloads` if they exist. Pass `knowledge=False` to disable this.

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

## Architecture

```
simon/
├── agent/          # Agent — the only required entry point
├── config/         # Settings loaded from .env via pydantic-settings
├── knowledge/      # Chunking, embedding, and retrieval (numpy-backed)
├── memory/         # Base class + InMemoryMemory implementation
├── models/         # Provider wrappers: OpenAI, Anthropic, Ollama, Echo
├── router/         # ModelRouter — provider selection logic
└── tools/
    ├── tool.py     # @tool decorator + ToolRegistry
    └── builtin/    # datetime_now, fs_*, shell_run, web_search, http_get
```

### Core concepts

1. **`Agent`** — the single public entry point. Wires memory, knowledge, tools, and a model together.
2. **`Memory`** — pluggable conversation history. Default: `InMemoryMemory` (in-process list). Implement `BaseMemory` to add persistence.
3. **`KnowledgeBase`** — ingest documents, chunk them, embed with the configured provider, and retrieve by cosine similarity at query time. Index files are stored in `.simon_knowledge/`.
4. **`@tool`** — a decorator that turns any typed Python function into a callable tool with an auto-generated JSON schema.
5. **`ModelRouter`** — selects the right provider at runtime based on available API keys, the `DEFAULT_MODEL` env var, and a simple task-complexity heuristic.

### Async support

`Agent.run()` is a synchronous convenience wrapper around `Agent.run_async()`. In async contexts (e.g., FastAPI, Jupyter with a running event loop), use `await agent.run_async(prompt)` directly.

---

## Running the tests

```bash
# activate your environment first
conda activate simon   # or: source .venv/bin/activate

pytest
```

Tests live in `tests/`. They use `pytest-asyncio` for async test cases.

---

## Non-goals (v1)

The following are intentionally out of scope:

- Multi-agent systems and agent orchestration
- Workflow engines and event buses
- Distributed execution
- MCP integration
- Docker / Kubernetes requirements
- GUI / TUI layers
- Enterprise features (auth, RBAC, audit logs, …)
