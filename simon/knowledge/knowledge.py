from pathlib import Path

from simon.knowledge.retrieval import Retriever


class KnowledgeBase:
    """Document ingestion + retrieval with hidden implementation details."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self._retriever = Retriever()
        self.chunk_size = chunk_size
        self.overlap = overlap

    def add(self, path: str) -> int:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Knowledge path not found: {path}")

        files = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file()]
        count = 0
        for file in files:
            text = self._read_file(file)
            for chunk in self._chunk(text):
                self._retriever.add_chunk(chunk, source=str(file))
                count += 1
        return count

    def search(self, query: str, top_k: int = 3) -> list[dict[str, str]]:
        return self._retriever.search(query, top_k=top_k)

    def _chunk(self, text: str) -> list[str]:
        if not text.strip():
            return []

        chunks: list[str] = []
        step = max(1, self.chunk_size - self.overlap)
        for i in range(0, len(text), step):
            chunk = text[i : i + self.chunk_size].strip()
            if chunk:
                chunks.append(chunk)
        return chunks

    def _read_file(self, path: Path) -> str:
        if path.suffix.lower() == ".pdf":
            try:
                from pypdf import PdfReader
            except ImportError as exc:
                raise RuntimeError("Install pypdf to ingest PDF files.") from exc

            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)

        return path.read_text(encoding="utf-8", errors="ignore")
