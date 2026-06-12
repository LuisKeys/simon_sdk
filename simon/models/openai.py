import json

from simon.agent.response import AgentResponse, ToolCall, Usage
from simon.exceptions import ProviderError
from simon.models.base import BaseModel
from simon.config import settings


def _to_openai_messages(messages: list[dict[str, object]]) -> list[dict[str, object]]:
    """Translate Simon's generic message format to the OpenAI chat format.

    Handles plain {role, content} dicts plus two tool-loop shapes produced by
    the Agent: assistant turns carrying ``tool_calls`` and ``{"role": "tool"}``
    result messages.
    """

    out: list[dict[str, object]] = []
    for m in messages:
        if m["role"] == "assistant" and m.get("tool_calls"):
            calls = m["tool_calls"]  # type: ignore[assignment]
            out.append(
                {
                    "role": "assistant",
                    "content": m.get("content") or None,
                    "tool_calls": [
                        {
                            "id": c.id,
                            "type": "function",
                            "function": {
                                "name": c.name,
                                "arguments": json.dumps(c.arguments),
                            },
                        }
                        for c in calls
                    ],
                }
            )
        elif m["role"] == "tool":
            out.append(
                {
                    "role": "tool",
                    "tool_call_id": m["tool_call_id"],
                    "content": str(m["content"]),
                }
            )
        else:
            out.append({"role": m["role"], "content": m["content"]})
    return out


class OpenAIModel(BaseModel):
    def __init__(self, model: str = "gpt-5") -> None:
        self.model = model

    async def complete(
        self,
        messages: list[dict[str, object]],
        tools: list[dict[str, object]] | None = None,
    ) -> AgentResponse:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise ProviderError("Install openai package to use OpenAIModel.") from exc

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        kwargs: dict[str, object] = {
            "model": self.model,
            "messages": _to_openai_messages(messages),
        }
        if tools:
            kwargs["tools"] = [{"type": "function", "function": t} for t in tools]
        response = await client.chat.completions.create(**kwargs)  # type: ignore[arg-type]

        choice = response.choices[0]
        message = choice.message
        text = message.content or ""

        tool_calls: list[ToolCall] = []
        for call in message.tool_calls or []:
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}
            tool_calls.append(
                ToolCall(id=call.id, name=call.function.name, arguments=arguments)
            )

        usage = None
        if response.usage:
            usage = Usage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
        return AgentResponse(
            text=text,
            usage=usage,
            tool_calls=tool_calls,
            stop_reason=choice.finish_reason,
        )
