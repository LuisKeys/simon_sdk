from simon.models import AnthropicModel, EchoModel, OllamaModel, OpenAIModel
from simon.router import ModelRouter


def test_router_default_is_model() -> None:
    model = ModelRouter().resolve()
    assert model is not None


def test_router_explicit_prefixes(monkeypatch) -> None:
    monkeypatch.setattr("simon.router.router.settings.openai_api_key", "test-key")
    monkeypatch.setattr("simon.router.router.settings.openai_model", "gpt-5")
    monkeypatch.setattr("simon.router.router.settings.anthropic_api_key", "test-key")
    monkeypatch.setattr(
        "simon.router.router.settings.anthropic_model", "claude-3-5-sonnet-latest"
    )
    monkeypatch.setattr("simon.router.router.settings.ollama_model", "llama3.1")
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434")

    assert isinstance(ModelRouter().resolve("gpt-5"), OpenAIModel)
    assert isinstance(ModelRouter().resolve("claude-3-5-sonnet-latest"), AnthropicModel)
    assert isinstance(ModelRouter().resolve("llama3.1"), OllamaModel)


def test_echo_model_type() -> None:
    assert isinstance(EchoModel(), EchoModel)


def test_router_auto_prefers_ollama_when_available(
    monkeypatch,
) -> None:
    monkeypatch.setattr("simon.router.router.settings.openai_api_key", "test-key")
    monkeypatch.setattr("simon.router.router.settings.openai_model", "gpt-5.4-mini")
    monkeypatch.setattr("simon.router.router.settings.anthropic_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_model", "")
    monkeypatch.setattr("simon.router.router.settings.ollama_model", "gemma4:e4b")
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434")

    assert isinstance(ModelRouter().resolve("auto"), OllamaModel)


def test_router_auto_prefers_online_for_complex_tasks(monkeypatch) -> None:
    monkeypatch.setattr("simon.router.router.settings.openai_api_key", "test-key")
    monkeypatch.setattr("simon.router.router.settings.openai_model", "gpt-5.4-mini")
    monkeypatch.setattr("simon.router.router.settings.anthropic_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_model", "")
    monkeypatch.setattr("simon.router.router.settings.ollama_model", "gemma4:e4b")
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434")

    model = ModelRouter().resolve("auto", task="Please do deep reasoning and analysis")
    assert isinstance(model, OpenAIModel)


def test_router_auto_uses_ollama_when_only_ollama_configured(monkeypatch) -> None:
    monkeypatch.setattr("simon.router.router.settings.openai_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.openai_model", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_model", "")
    monkeypatch.setattr("simon.router.router.settings.ollama_model", "gemma4:e4b")
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434")

    assert isinstance(ModelRouter().resolve("auto"), OllamaModel)


def test_router_skips_unconfigured_anthropic(monkeypatch) -> None:
    monkeypatch.setattr("simon.router.router.settings.openai_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.openai_model", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_model", "")
    monkeypatch.setattr("simon.router.router.settings.ollama_model", "")
    monkeypatch.delenv("OLLAMA_HOST", raising=False)

    assert isinstance(ModelRouter().resolve("claude-3-5-sonnet-latest"), EchoModel)


def test_router_skips_provider_without_model(monkeypatch) -> None:
    monkeypatch.setattr("simon.router.router.settings.openai_api_key", "test-key")
    monkeypatch.setattr("simon.router.router.settings.openai_model", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.anthropic_model", "")
    monkeypatch.setattr("simon.router.router.settings.ollama_model", "")
    monkeypatch.delenv("OLLAMA_HOST", raising=False)

    assert isinstance(ModelRouter().resolve("auto"), EchoModel)


def test_router_uses_openai_model_from_settings(monkeypatch) -> None:
    monkeypatch.setattr("simon.router.router.settings.openai_api_key", "test-key")
    monkeypatch.setattr("simon.router.router.settings.openai_model", "gpt-5.4-mini")

    model = ModelRouter().resolve("gpt-5")

    assert isinstance(model, OpenAIModel)
    assert model.model == "gpt-5.4-mini"


def test_router_forces_default_model_provider_when_non_auto(monkeypatch) -> None:
    monkeypatch.setattr("simon.router.router.settings.default_model", "gpt-5")
    monkeypatch.setattr("simon.router.router.settings.openai_api_key", "test-key")
    monkeypatch.setattr("simon.router.router.settings.openai_model", "gpt-5.4-mini")
    monkeypatch.setattr("simon.router.router.settings.ollama_model", "gemma4:e4b")
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434")

    model = ModelRouter().resolve(task="simple local task")
    assert isinstance(model, OpenAIModel)


def test_router_forced_default_model_does_not_fallback(monkeypatch) -> None:
    monkeypatch.setattr("simon.router.router.settings.default_model", "gpt-5")
    monkeypatch.setattr("simon.router.router.settings.openai_api_key", "")
    monkeypatch.setattr("simon.router.router.settings.openai_model", "")
    monkeypatch.setattr("simon.router.router.settings.ollama_model", "gemma4:e4b")
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434")

    model = ModelRouter().resolve(task="simple local task")
    assert isinstance(model, EchoModel)
