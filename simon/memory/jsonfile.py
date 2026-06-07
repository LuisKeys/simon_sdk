import json
from pathlib import Path

from simon.memory.base import BaseMemory


_CHATS_DIR = Path(".simon_chats")


class JSONFileMemory(BaseMemory):
    """Persistent conversation history backed by a single JSON file.

    All files are stored under ``.simon_chats/``. Pass only a filename (no
    directory) to name the conversation, e.g. ``JSONFileMemory("support.json")``.
    If no name is given, the default is ``conversation.json``.

    The file is a human-readable JSON list of ``{"role", "content"}`` objects,
    so it can be inspected, versioned, copied, or deleted by hand.
    """

    def __init__(self, name: str = "conversation.json") -> None:
        self._path = _CHATS_DIR / Path(name).name
        self._messages: list[dict[str, str]] | None = None

    def _load(self) -> list[dict[str, str]]:
        if self._messages is None:
            if self._path.exists():
                with self._path.open("r", encoding="utf-8") as fh:
                    self._messages = json.load(fh)
            else:
                self._messages = []
        return self._messages

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as fh:
            json.dump(self._messages or [], fh, indent=2, ensure_ascii=False)

    async def add(self, role: str, content: str) -> None:
        self._load().append({"role": role, "content": content})
        self._save()

    async def list(self) -> list[dict[str, str]]:
        return list(self._load())

    async def clear(self) -> None:
        self._messages = []
        self._save()
