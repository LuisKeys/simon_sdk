import asyncio

import pytest

from simon.reliability import with_retry


def test_retries_then_succeeds() -> None:
    calls = {"n": 0}

    async def factory():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("transient")
        return "ok"

    result = asyncio.run(
        with_retry(factory, retries=3, base_delay=0.0, timeout=None)
    )
    assert result == "ok"
    assert calls["n"] == 3


def test_raises_after_exhausting_retries() -> None:
    calls = {"n": 0}

    async def factory():
        calls["n"] += 1
        raise ValueError("always fails")

    with pytest.raises(ValueError, match="always fails"):
        asyncio.run(with_retry(factory, retries=2, base_delay=0.0, timeout=None))
    assert calls["n"] == 3  # 1 initial + 2 retries


def test_timeout_triggers_retry() -> None:
    calls = {"n": 0}

    async def factory():
        calls["n"] += 1
        if calls["n"] == 1:
            await asyncio.sleep(10)  # exceeds timeout -> TimeoutError
        return "recovered"

    result = asyncio.run(
        with_retry(factory, retries=1, base_delay=0.0, timeout=0.05)
    )
    assert result == "recovered"
    assert calls["n"] == 2
