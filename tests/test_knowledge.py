from pathlib import Path

from simon.knowledge import KnowledgeBase


def test_knowledge_ingestion_and_search(tmp_path: Path) -> None:
    doc = tmp_path / "doc.txt"
    doc.write_text(
        "Neural networks are universal function approximators.", encoding="utf-8"
    )

    kb = KnowledgeBase(chunk_size=40, overlap=5)
    count = kb.add(str(doc))
    assert count > 0

    hits = kb.search("function approximators", top_k=1)
    assert len(hits) == 1
    assert "doc.txt" in hits[0]["source"]
