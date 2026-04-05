"""Retry utilities for transient integration failures."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar


T = TypeVar("T")


async def with_retry(
    operation: Callable[[], Awaitable[T]],
    retries: int = 3,
    base_delay: float = 0.5,
) -> T:
    """Run an async operation with exponential backoff."""
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            return await operation()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == retries - 1:
                break
            await asyncio.sleep(base_delay * (2**attempt))
    raise RuntimeError(f"Operation failed after {retries} attempts") from last_error
