from dataclasses import dataclass, field


@dataclass
class Usage:
    input_tokens: int
    output_tokens: int
    total_tokens: int


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

    def __str__(self) -> str:
        return self.text
