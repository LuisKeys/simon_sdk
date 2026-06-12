"""Helpers for structured / schema-constrained agent output."""

import json
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    import pydantic


def schema_instruction(output_model: type) -> str:
    """Build a system message instructing the model to return JSON matching the schema."""
    schema = output_model.model_json_schema()  # type: ignore[attr-defined]
    return (
        "Respond with ONLY a JSON object matching this JSON schema. "
        "No prose, no markdown fences, no explanation — just the raw JSON object:\n"
        + json.dumps(schema, indent=2)
    )


def parse_structured(text: str, output_model: type) -> Any:
    """Parse *text* into a validated instance of *output_model*.

    Strips common LLM decorations (```json fences, leading/trailing prose)
    before attempting validation. Raises ``pydantic.ValidationError`` or
    ``json.JSONDecodeError`` on failure so the caller can decide how to retry.
    """
    candidate = text.strip()

    # Strip ```json ... ``` or ``` ... ``` fences
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        # drop first and last fence lines
        inner = lines[1:] if lines[0].startswith("```") else lines
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        candidate = "\n".join(inner).strip()

    # Slice from first '{' to last '}' as a fallback for prose wrapping
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start != -1 and end != -1 and end >= start:
        candidate = candidate[start : end + 1]

    return output_model.model_validate_json(candidate)  # type: ignore[attr-defined]
