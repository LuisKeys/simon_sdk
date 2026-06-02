import math

from simon.config.settings import settings


class OpenAIEmbeddings:
    """Dense semantic embeddings via the OpenAI embeddings API."""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        from openai import OpenAI

        self._model = model or settings.embedding_model
        self._client = OpenAI(api_key=api_key or settings.openai_api_key)

    def embed(self, text: str) -> list[float]:
        return self._normalize(
            self._client.embeddings.create(input=[text], model=self._model)
            .data[0]
            .embedding
        )

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(input=texts, model=self._model)
        return [self._normalize(item.embedding) for item in response.data]

    @staticmethod
    def _normalize(vec: list[float]) -> list[float]:
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]
