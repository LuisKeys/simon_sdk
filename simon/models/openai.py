from simon.models.base import BaseModel


class OpenAIModel(BaseModel):
    def __init__(self, model: str = "gpt-5") -> None:
        self.model = model

    async def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, object]] | None = None,
    ) -> str:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise RuntimeError("Install openai package to use OpenAIModel.") from exc

        client = AsyncOpenAI()
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore[arg-type]
            tools=[{"type": "function", "function": t} for t in (tools or [])],
        )
        return response.choices[0].message.content or ""
