import asyncio
import logging
from typing import Awaitable, Callable, TypeVar

logger = logging.getLogger("simon.reliability")

T = TypeVar("T")


async def with_retry(
    coro_factory: Callable[[], Awaitable[T]],
    *,
    retries: int = 2,
    base_delay: float = 0.5,
    timeout: float | None = 60.0,
    on_retry: Callable[[int, BaseException], None] | None = None,
) -> T:
    """Run an awaitable with a per-attempt timeout and exponential backoff.

    ``coro_factory`` must return a *fresh* awaitable on each call, since a
    coroutine can only be awaited once. It is retried up to ``retries`` extra
    times (so ``retries + 1`` total attempts) on timeout or any exception,
    waiting ``base_delay * 2**n`` seconds between attempts.

    ``on_retry`` is called with ``(attempt_number, exception)`` just before
    each retry sleep, useful for observability hooks.
    """

    attempts = retries + 1
    last_exc: BaseException | None = None
    for attempt in range(attempts):
        try:
            if timeout is not None:
                return await asyncio.wait_for(coro_factory(), timeout=timeout)
            return await coro_factory()
        except Exception as exc:  # noqa: BLE001 - retry on any transient failure
            last_exc = exc
            if attempt + 1 >= attempts:
                break
            delay = base_delay * (2**attempt)
            logger.warning(
                "attempt %d/%d failed (%s: %s); retrying in %.2fs",
                attempt + 1,
                attempts,
                type(exc).__name__,
                exc,
                delay,
            )
            if on_retry is not None:
                try:
                    on_retry(attempt + 1, exc)
                except Exception:
                    pass
            await asyncio.sleep(delay)

    assert last_exc is not None
    raise last_exc
