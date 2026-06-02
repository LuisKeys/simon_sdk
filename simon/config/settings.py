from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings with sensible defaults."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    openai_api_key: str | None = None
    openai_model: str | None = None
    anthropic_api_key: str | None = None
    anthropic_model: str | None = None
    ollama_host: str = "http://localhost:11434"
    ollama_model: str | None = None
    default_model: str = "auto"
    knowledge_store_path: str | None = None
    embedding_model: str = "text-embedding-3-small"


settings = Settings()
