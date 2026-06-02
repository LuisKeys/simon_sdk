from simon.knowledge.embeddings import SimpleEmbeddings


class Retriever:
    """In-memory vector retrieval over chunked documents."""

    def __init__(self, embeddings: SimpleEmbeddings | None = None) -> None:
        self._embeddings = embeddings or SimpleEmbeddings()
        self._chunks: list[dict[str, object]] = []

    def add_chunk(self, text: str, source: str) -> None:
        vector = self._embeddings.embed(text)
        self._chunks.append({"text": text, "source": source, "vector": vector})

    def search(self, query: str, top_k: int = 3) -> list[dict[str, str]]:
        qvec = self._embeddings.embed(query)

        def cosine_sparse(a: dict[str, float], b: dict[str, float]) -> float:
            return sum(a.get(k, 0.0) * b.get(k, 0.0) for k in a.keys())

        scored: list[tuple[float, dict[str, object]]] = []
        for chunk in self._chunks:
            score = cosine_sparse(qvec, chunk["vector"])  # type: ignore[index]
            scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        out: list[dict[str, str]] = []
        for score, chunk in scored[:top_k]:
            out.append(
                {
                    "text": str(chunk["text"]),
                    "source": str(chunk["source"]),
                    "score": f"{score:.3f}",
                }
            )
        return out
