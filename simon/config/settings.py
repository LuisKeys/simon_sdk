import logging

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
    embedding_provider: str = "OPENAI"
    embedding_model: str = "text-embedding-3-small"
    enable_dir_documents: bool = True
    enable_dir_downloads: bool = True
    enable_dir_pictures: bool = False
    enable_dir_desktop: bool = False
    simon_logging_enabled: bool = False
    simon_log_level: str = "INFO"
    simon_max_retries: int = 2
    simon_request_timeout: float = 60.0
    simon_retry_base_delay: float = 0.5
    simon_structured_retries: int = 2

    def model_post_init(self, __context: object) -> None:
        if self.simon_logging_enabled:
            logging.basicConfig(
                level=getattr(logging, self.simon_log_level.upper(), logging.INFO),
                format="%(name)s | %(message)s",
            )


settings = Settings()
