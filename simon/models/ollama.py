from simon.agent.response import AgentResponse
from simon.exceptions import ProviderError
from simon.models.base import BaseModel


class OllamaModel(BaseModel):
    def __init__(self, model: str = "llama3.1") -> None:
        self.model = model

    async def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, object]] | None = None,
    ) -> AgentResponse:
        _ = tools
        try:
            from ollama import AsyncClient
        except ImportError as exc:
            raise ProviderError("Install ollama package to use OllamaModel.") from exc

        client = AsyncClient()
        response = await client.chat(model=self.model, messages=messages)
        msg = response.get("message", {})
        return AgentResponse(text=str(msg.get("content", "")))
