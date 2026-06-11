from simon.agent.response import AgentResponse, ToolCall, Usage
from simon.models.base import BaseModel


def _split_messages(
    messages: list[dict[str, object]],
) -> tuple[str, list[dict[str, object]]]:
    """Return (system_prompt, anthropic_messages) from Simon's generic format.

    System messages are concatenated into a single system string. Assistant
    turns with ``tool_calls`` become ``tool_use`` content blocks and
    ``{"role": "tool"}`` messages become ``tool_result`` blocks on a user turn.
    """

    system_parts: list[str] = []
    converted: list[dict[str, object]] = []
    for m in messages:
        role = m["role"]
        if role == "system":
            system_parts.append(str(m["content"]))
        elif role == "assistant" and m.get("tool_calls"):
            blocks: list[dict[str, object]] = []
            if m.get("content"):
                blocks.append({"type": "text", "text": str(m["content"])})
            for c in m["tool_calls"]:  # type: ignore[union-attr]
                blocks.append(
                    {
                        "type": "tool_use",
                        "id": c.id,
                        "name": c.name,
                        "input": c.arguments,
                    }
                )
            converted.append({"role": "assistant", "content": blocks})
        elif role == "tool":
            converted.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": m["tool_call_id"],
                            "content": str(m["content"]),
                        }
                    ],
                }
            )
        else:
            converted.append({"role": role, "content": str(m["content"])})
    return "\n".join(system_parts), converted


class AnthropicModel(BaseModel):
    def __init__(self, model: str = "claude-3-5-sonnet-latest") -> None:
        self.model = model

    async def complete(
        self,
        messages: list[dict[str, object]],
        tools: list[dict[str, object]] | None = None,
    ) -> AgentResponse:
        try:
            from anthropic import AsyncAnthropic
        except ImportError as exc:
            raise RuntimeError(
                "Install anthropic package to use AnthropicModel."
            ) from exc

        client = AsyncAnthropic()

        system, anthropic_messages = _split_messages(messages)
        kwargs: dict[str, object] = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": anthropic_messages,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        response = await client.messages.create(**kwargs)  # type: ignore[arg-type]

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in response.content:
            btype = getattr(block, "type", "")
            if btype == "text":
                text_parts.append(getattr(block, "text", ""))
            elif btype == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=dict(block.input or {}),
                    )
                )
        text = "\n".join(text_parts).strip()
        usage = Usage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
        )
        return AgentResponse(
            text=text,
            usage=usage,
            tool_calls=tool_calls,
            stop_reason=response.stop_reason,
        )
