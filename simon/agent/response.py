from dataclasses import dataclass


@dataclass
class Usage:
    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass
class AgentResponse:
    text: str
    usage: Usage | None = None  # None for local/free providers (Ollama, Echo)

    def __str__(self) -> str:
        return self.text
