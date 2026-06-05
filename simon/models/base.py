from abc import ABC, abstractmethod

from simon.agent.response import AgentResponse


class BaseModel(ABC):
    """Abstract model adapter."""

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, object]] | None = None,
    ) -> AgentResponse:
        raise NotImplementedError


class EchoModel(BaseModel):
    """Safe default when no provider is configured."""

    async def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, object]] | None = None,
    ) -> AgentResponse:
        _ = tools
        user_message = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        return AgentResponse(text=f"Simon (echo): {user_message}")
