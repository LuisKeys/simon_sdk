import hashlib
import pickle
from pathlib import Path

import numpy as np

from simon.knowledge.embeddings import OpenAIEmbeddings


class FileRetriever:
    """Persistent vector retrieval backed by numpy binary files."""

    def __init__(self, embeddings: OpenAIEmbeddings, store_path: str | Path) -> None:
        self._embeddings = embeddings
        self._store = Path(store_path)
        self._store.mkdir(parents=True, exist_ok=True)
        self._matrices: dict[str, np.ndarray] = {}
        self._load_existing()

    def _load_existing(self) -> None:
        for npy_file in self._store.glob("*.npy"):
            key = npy_file.stem
            self._matrices[key] = np.load(npy_file)

    def _key(self, source: str) -> str:
        return hashlib.sha256(source.encode()).hexdigest()[:16]

    def add_source(self, texts: list[str], source: str, force: bool = False) -> None:
        key = self._key(source)
        if key in self._matrices:
            if not force:
                return
            (self._store / f"{key}.npy").unlink(missing_ok=True)
            (self._store / f"{key}.meta").unlink(missing_ok=True)
            del self._matrices[key]

        vectors = self._embeddings.embed_batch(texts)
        matrix = np.array(vectors, dtype=np.float32)

        np.save(self._store / f"{key}.npy", matrix)
        meta = [{"text": t, "source": source} for t in texts]
        with open(self._store / f"{key}.meta", "wb") as f:
            pickle.dump(meta, f)

        self._matrices[key] = matrix

    def search(self, query: str, top_k: int = 3) -> list[dict[str, str]]:
        if not self._matrices:
            return []
        qvec = np.array(self._embeddings.embed(query), dtype=np.float32)

        results: list[tuple[float, str, int]] = []
        for key, matrix in self._matrices.items():
            scores = matrix @ qvec
            for i, score in enumerate(scores):
                results.append((float(score), key, int(i)))

        results.sort(reverse=True)
        out: list[dict[str, str]] = []
        for score, key, idx in results[:top_k]:
            meta_path = self._store / f"{key}.meta"
            with open(meta_path, "rb") as f:
                meta = pickle.load(f)
            chunk = meta[idx]
            out.append(
                {
                    "text": chunk["text"],
                    "source": chunk["source"],
                    "score": f"{score:.3f}",
                }
            )
        return out
