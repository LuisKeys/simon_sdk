from simon.config import settings
from simon.models import AnthropicModel, BaseModel, EchoModel, OllamaModel, OpenAIModel


class ModelRouter:
    """Lightweight model/provider selection with sensible defaults."""

    def resolve(self, model: str | None = None) -> BaseModel:
        selected = (model or settings.default_model or "auto").lower()

        if selected.startswith("gpt") or selected.startswith("openai"):
            return OpenAIModel(model=model or "gpt-5")
        if selected.startswith("claude") or selected.startswith("anthropic"):
            return AnthropicModel(model=model or "claude-3-5-sonnet-latest")
        if selected.startswith("ollama") or selected.startswith("llama"):
            name = "llama3.1" if selected == "ollama" else (model or "llama3.1")
            return OllamaModel(model=name)

        if settings.openai_api_key:
            return OpenAIModel(model="gpt-5")
        if settings.anthropic_api_key:
            return AnthropicModel(model="claude-3-5-sonnet-latest")

        return EchoModel()
