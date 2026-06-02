from abc import ABC, abstractmethod


class BaseMemory(ABC):
    """Minimal memory protocol for conversation history."""

    @abstractmethod
    async def add(self, role: str, content: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list(self) -> list[dict[str, str]]:
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        raise NotImplementedError
