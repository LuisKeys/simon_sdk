from pathlib import Path

from simon import Agent

PROMPT = """
You are a friendly professor explaining AI concepts to a curious 20-year-old.
Using only the document you have been given, explain the following topics.
Keep each answer under 3 sentences. Avoid all math and jargon — use simple
real-world analogies wherever possible.

1. What is a Transformer model and what problem does it solve?
2. What does "attention" mean in this context? Give a simple real-world analogy.
3. What do the encoder and decoder do? (one sentence each)
4. What is multi-head attention, in plain English?
5. Why is positional encoding needed and how can we think about it simply?
"""

if __name__ == "__main__":
    paper_path = Path(__file__).parent / "docs" / "attention_paper.pdf"

    agent = Agent()
    chunks = agent.knowledge.add(
        str(paper_path)
    )  # returns number of new chunks indexed
    if chunks:
        print(f"Indexed {chunks} chunks from {paper_path.name}\n")
    else:
        print(f"{paper_path.name} already indexed — skipping.\n")
    # To force re-indexing: agent.knowledge.add(str(paper_path), force=True)
    print(agent.run(PROMPT))
