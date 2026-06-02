from simon.models import AnthropicModel, EchoModel, OllamaModel, OpenAIModel
from simon.router import ModelRouter


def test_router_default_is_model() -> None:
    model = ModelRouter().resolve()
    assert model is not None


def test_router_explicit_prefixes() -> None:
    assert isinstance(ModelRouter().resolve("gpt-5"), OpenAIModel)
    assert isinstance(ModelRouter().resolve("claude-3-5-sonnet-latest"), AnthropicModel)
    assert isinstance(ModelRouter().resolve("llama3.1"), OllamaModel)


def test_echo_model_type() -> None:
    assert isinstance(EchoModel(), EchoModel)
