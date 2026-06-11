from abc import ABC, abstractmethod

from simon.agent.response import AgentResponse


class BaseModel(ABC):
    """Abstract model adapter."""

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, object]],
        tools: list[dict[str, object]] | None = None,
    ) -> AgentResponse:
        """Return the model's reply.

        When ``tools`` are provided the model may request tool calls by
        populating ``AgentResponse.tool_calls``; the Agent's ReAct loop runs
        them and feeds the results back. Models that cannot call tools simply
        leave ``tool_calls`` empty (the default), so the loop runs once.
        """
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
