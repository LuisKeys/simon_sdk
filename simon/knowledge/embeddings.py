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


class OllamaEmbeddings:
    """Dense semantic embeddings via a local Ollama server."""

    def __init__(self, model: str | None = None) -> None:
        self._model = model or settings.ollama_model or "nomic-embed-text"
        self._host = settings.ollama_host

    def embed(self, text: str) -> list[float]:
        return self._normalize(self._embed_one(text))

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._normalize(self._embed_one(t)) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        try:
            from ollama import Client
        except ImportError as exc:
            raise RuntimeError("Install ollama package to use OllamaEmbeddings.") from exc

        client = Client(host=self._host)
        response = client.embeddings(model=self._model, prompt=text)
        return response["embedding"]

    @staticmethod
    def _normalize(vec: list[float]) -> list[float]:
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


def default_embeddings():
    """Return the best available embeddings provider.

    Prefers Ollama when a local server is configured; falls back to OpenAI.
    """
    if settings.ollama_host:
        return OllamaEmbeddings()
    if settings.openai_api_key:
        return OpenAIEmbeddings()
    raise RuntimeError(
        "No embeddings provider available. "
        "Set OPENAI_API_KEY or configure an Ollama server via OLLAMA_HOST."
    )
