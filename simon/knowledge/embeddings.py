import math
import re


class SimpleEmbeddings:
    """Tiny deterministic embedding model based on token frequency."""

    def embed(self, text: str) -> dict[str, float]:
        counts: dict[str, float] = {}
        for token in re.findall(r"[a-zA-Z0-9_]+", text.lower()):
            counts[token] = counts.get(token, 0.0) + 1.0

        norm = math.sqrt(sum(v * v for v in counts.values())) or 1.0
        return {k: v / norm for k, v in counts.items()}
