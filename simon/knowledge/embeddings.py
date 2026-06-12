import math

from simon.config.settings import settings
from simon.exceptions import KnowledgeError


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


class OllamaEmbeddings:
    """Dense semantic embeddings via a local Ollama server."""

    def __init__(self, model: str | None = None) -> None:
        self._model = model or settings.embedding_model
        self._host = settings.ollama_host

    def embed(self, text: str) -> list[float]:
        return self._normalize(self._embed_one(text))

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._normalize(self._embed_one(t)) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        try:
            from ollama import Client
        except ImportError as exc:
            raise KnowledgeError("Install ollama package to use OllamaEmbeddings.") from exc

        client = Client(host=self._host)
        response = client.embeddings(model=self._model, prompt=text)
        return response["embedding"]

    @staticmethod
    def _normalize(vec: list[float]) -> list[float]:
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


class AnthropicEmbeddings:
    """Dense semantic embeddings via Voyage AI (Anthropic's recommended embeddings provider)."""

    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        try:
            import voyageai
        except ImportError as exc:
            raise KnowledgeError(
                "Install voyageai package to use AnthropicEmbeddings: pip install voyageai"
            ) from exc

        self._model = model or settings.embedding_model
        self._client = voyageai.Client(api_key=api_key or settings.anthropic_api_key)

    def embed(self, text: str) -> list[float]:
        result = self._client.embed([text], model=self._model)
        return self._normalize(result.embeddings[0])

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        result = self._client.embed(texts, model=self._model)
        return [self._normalize(e) for e in result.embeddings]

    @staticmethod
    def _normalize(vec: list[float]) -> list[float]:
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


def default_embeddings():
    """Return the embeddings provider configured via EMBEDDING_PROVIDER."""
    provider = settings.embedding_provider.upper()
    if provider == "OLLAMA":
        return OllamaEmbeddings()
    if provider == "ANTHROPIC":
        return AnthropicEmbeddings()
    if provider == "OPENAI":
        return OpenAIEmbeddings()
    raise KnowledgeError(
        f"Unknown EMBEDDING_PROVIDER '{provider}'. Valid values: OPENAI, OLLAMA, ANTHROPIC."
    )
