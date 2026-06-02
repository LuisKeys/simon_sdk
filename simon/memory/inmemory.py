from simon.memory.base import BaseMemory


class InMemoryMemory(BaseMemory):
    """Simple in-memory storage designed to be replaceable later."""

    def __init__(self) -> None:
        self._messages: list[dict[str, str]] = []

    async def add(self, role: str, content: str) -> None:
        self._messages.append({"role": role, "content": content})

    async def list(self) -> list[dict[str, str]]:
        return list(self._messages)

    async def clear(self) -> None:
        self._messages.clear()
