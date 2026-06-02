import os

from simon.config import settings
from simon.models import AnthropicModel, BaseModel, EchoModel, OllamaModel, OpenAIModel


class ModelRouter:
    """Lightweight model/provider selection with sensible defaults."""

    _COMPLEX_TASK_HINTS = (
        "complex",
        "difficult",
        "hard",
        "multi-step",
        "reasoning",
        "analyze",
        "analysis",
        "arquitectura",
        "arquitectónico",
        "complej",
        "razonamiento",
        "profundo",
    )

    @staticmethod
    def _has_openai() -> bool:
        return bool((settings.openai_api_key or "").strip()) and bool(
            (settings.openai_model or "").strip()
        )

    @staticmethod
    def _has_anthropic() -> bool:
        return bool((settings.anthropic_api_key or "").strip()) and bool(
            (settings.anthropic_model or "").strip()
        )

    @staticmethod
    def _has_ollama() -> bool:
        # Treat Ollama as configured only when OLLAMA_HOST is explicitly provided
        # and an Ollama model name is configured.
        host = os.getenv("OLLAMA_HOST")
        return bool((host or "").strip()) and bool(
            (settings.ollama_model or "").strip()
        )

    @classmethod
    def _is_complex_task(cls, task: str | None) -> bool:
        if not task:
            return False
        text = task.lower()
        return any(hint in text for hint in cls._COMPLEX_TASK_HINTS)

    def resolve(
        self,
        model: str | None = None,
        task: str | None = None,
        complex_task: bool | None = None,
    ) -> BaseModel:
        default_selected = (settings.default_model or "auto").lower()
        force_default_provider = model is None and default_selected != "auto"
        selected = (model or default_selected).lower()
        is_complex = (
            self._is_complex_task(task) if complex_task is None else complex_task
        )

        if (
            selected.startswith("gpt") or selected.startswith("openai")
        ) and self._has_openai():
            return OpenAIModel(model=settings.openai_model or "gpt-5")
        if (
            selected.startswith("claude") or selected.startswith("anthropic")
        ) and self._has_anthropic():
            return AnthropicModel(
                model=settings.anthropic_model or "claude-3-5-sonnet-latest"
            )
        if (
            selected.startswith("ollama") or selected.startswith("llama")
        ) and self._has_ollama():
            return OllamaModel(model=settings.ollama_model or "llama3.1")

        if force_default_provider:
            # When DEFAULT_MODEL is explicitly set (non-auto), do not fallback
            # to other providers.
            return EchoModel()

        if is_complex:
            # For harder tasks, prioritize online providers when available.
            if self._has_openai():
                return OpenAIModel(model=settings.openai_model or "gpt-5")
            if self._has_anthropic():
                return AnthropicModel(
                    model=settings.anthropic_model or "claude-3-5-sonnet-latest"
                )
            if self._has_ollama():
                return OllamaModel(model=settings.ollama_model or "llama3.1")
        else:
            # Default priority is local-first.
            if self._has_ollama():
                return OllamaModel(model=settings.ollama_model or "llama3.1")
            if self._has_openai():
                return OpenAIModel(model=settings.openai_model or "gpt-5")
            if self._has_anthropic():
                return AnthropicModel(
                    model=settings.anthropic_model or "claude-3-5-sonnet-latest"
                )

        return EchoModel()
