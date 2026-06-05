from simon.agent.response import AgentResponse, Usage
from simon.models.base import BaseModel


class AnthropicModel(BaseModel):
    def __init__(self, model: str = "claude-3-5-sonnet-latest") -> None:
        self.model = model

    async def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, object]] | None = None,
    ) -> AgentResponse:
        try:
            from anthropic import AsyncAnthropic
        except ImportError as exc:
            raise RuntimeError(
                "Install anthropic package to use AnthropicModel."
            ) from exc

        client = AsyncAnthropic()

        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        response = await client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
            tools=tools or [],
        )
        text_parts: list[str] = []
        for block in response.content:
            if getattr(block, "type", "") == "text":
                text_parts.append(getattr(block, "text", ""))
        text = "\n".join(text_parts).strip()
        usage = Usage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
        )
        return AgentResponse(text=text, usage=usage)
