"""Simon SDK exception hierarchy."""


class SimonError(Exception):
    """Base class for all Simon SDK errors."""


class ProviderError(SimonError, RuntimeError):
    """A model provider failed or its package is not installed."""


class ToolError(SimonError, ValueError):
    """A tool call was malformed or its execution failed."""


class KnowledgeError(SimonError, RuntimeError):
    """Knowledge base ingestion or configuration failed."""


class StructuredOutputError(SimonError):
    """The model never produced output matching the requested schema."""

    def __init__(self, message: str, *, raw_text: str = "", attempts: int = 0) -> None:
        super().__init__(message)
        self.raw_text = raw_text
        self.attempts = attempts
