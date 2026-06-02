import math
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

from simon.knowledge import KnowledgeBase


def _unit_vec(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


def _make_mock_embeddings(embed_vec: list[float]) -> MagicMock:
    mock = MagicMock()
    mock.embed.return_value = embed_vec
    mock.embed_batch.return_value = [embed_vec]
    return mock


def test_knowledge_ingestion_and_search(tmp_path: Path) -> None:
    doc = tmp_path / "doc.txt"
    doc.write_text(
        "Neural networks are universal function approximators.", encoding="utf-8"
    )

    vec = _unit_vec([1.0, 0.0, 0.0] + [0.0] * 1533)
    mock_emb = _make_mock_embeddings(vec)

    with patch("simon.knowledge.knowledge.OpenAIEmbeddings", return_value=mock_emb):
        kb = KnowledgeBase(chunk_size=40, overlap=5, store_path=str(tmp_path / "store"))
        count = kb.add(str(doc))

    assert count > 0

    mock_emb.embed.return_value = vec
    hits = kb.search("function approximators", top_k=1)
    assert len(hits) == 1
    assert "doc.txt" in hits[0]["source"]
