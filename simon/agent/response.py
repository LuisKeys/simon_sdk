from dataclasses import dataclass, field
from typing import Any


@dataclass
class Usage:
    input_tokens: int
    output_tokens: int
    total_tokens: int

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(
            self.input_tokens + other.input_tokens,
            self.output_tokens + other.output_tokens,
            self.total_tokens + other.total_tokens,
        )


@dataclass
class ToolCall:
    """A tool invocation requested by the model."""

    id: str
    name: str
    arguments: dict


@dataclass
class AgentResponse:
    text: str
    usage: Usage | None = None  # None for local/free providers (Ollama, Echo)
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str | None = None
    parsed: Any | None = None  # Validated pydantic instance when run(..., output_model=...) was used

    def __str__(self) -> str:
        return self.text
