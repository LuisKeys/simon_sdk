from simon.agent.response import AgentResponse, Usage
from simon.models.base import BaseModel
from simon.config import settings


class OpenAIModel(BaseModel):
    def __init__(self, model: str = "gpt-5") -> None:
        self.model = model

    async def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, object]] | None = None,
    ) -> AgentResponse:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise RuntimeError("Install openai package to use OpenAIModel.") from exc

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore[arg-type]
            tools=[{"type": "function", "function": t} for t in (tools or [])],
        )
        text = response.choices[0].message.content or ""
        usage = None
        if response.usage:
            usage = Usage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
        return AgentResponse(text=text, usage=usage)
