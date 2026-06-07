import asyncio
from pathlib import Path

import pytest

from simon.memory import JSONFileMemory
from simon.memory.jsonfile import _CHATS_DIR


@pytest.fixture(autouse=True)
def isolated_chats_dir(tmp_path, monkeypatch):
    """Redirect _CHATS_DIR to a temp path so tests don't pollute the workspace."""
    monkeypatch.setattr("simon.memory.jsonfile._CHATS_DIR", tmp_path / ".simon_chats")


def test_add_list_clear() -> None:
    mem = JSONFileMemory("conv.json")

    async def scenario():
        await mem.add("user", "hello")
        await mem.add("assistant", "hi there")
        assert await mem.list() == [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]
        await mem.clear()
        assert await mem.list() == []

    asyncio.run(scenario())


def test_persists_across_instances(tmp_path, monkeypatch) -> None:
    chats = tmp_path / ".simon_chats"
    monkeypatch.setattr("simon.memory.jsonfile._CHATS_DIR", chats)

    async def scenario():
        first = JSONFileMemory("conv.json")
        await first.add("user", "remember me")

        second = JSONFileMemory("conv.json")
        assert await second.list() == [{"role": "user", "content": "remember me"}]

    asyncio.run(scenario())
    assert (chats / "conv.json").exists()


def test_conversations_isolated_by_name() -> None:
    async def scenario():
        a = JSONFileMemory("a.json")
        b = JSONFileMemory("b.json")
        await a.add("user", "in a")
        await b.add("user", "in b")
        assert await a.list() == [{"role": "user", "content": "in a"}]
        assert await b.list() == [{"role": "user", "content": "in b"}]

    asyncio.run(scenario())


def test_creates_chats_directory(tmp_path, monkeypatch) -> None:
    chats = tmp_path / ".simon_chats"
    monkeypatch.setattr("simon.memory.jsonfile._CHATS_DIR", chats)

    async def scenario():
        mem = JSONFileMemory("conv.json")
        await mem.add("user", "hi")

    asyncio.run(scenario())
    assert (chats / "conv.json").exists()


def test_only_filename_is_used() -> None:
    """Path traversal is ignored — only the filename ends up in .simon_chats."""
    mem = JSONFileMemory("../../escaped.json")
    assert mem._path.name == "escaped.json"
    assert mem._path.parent.name == ".simon_chats" or str(mem._path).endswith(
        ".simon_chats/escaped.json"
    )
