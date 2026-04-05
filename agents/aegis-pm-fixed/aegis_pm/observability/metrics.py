"""In-process metrics registry with persistence."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path


class MetricsRegistry:
    """Track counters and latency samples for execution observability."""

    def __init__(self, path: Path) -> None:
        """Create a registry backed by a JSON file."""
        self.path = path
        self._lock = asyncio.Lock()
        self._state = {"counters": {}, "latencies": {}}
        if self.path.exists():
            self._state = json.loads(self.path.read_text(encoding="utf-8"))

    async def increment(self, metric: str, amount: int = 1) -> None:
        """Increment a counter metric."""
        async with self._lock:
            counters = self._state.setdefault("counters", {})
            counters[metric] = counters.get(metric, 0) + amount
            self._persist()

    async def observe_latency(self, metric: str, value_ms: float) -> None:
        """Append a latency observation for a metric."""
        async with self._lock:
            latencies = self._state.setdefault("latencies", {})
            latencies.setdefault(metric, []).append(value_ms)
            self._persist()

    async def snapshot(self) -> dict:
        """Return the current metrics snapshot."""
        async with self._lock:
            return json.loads(json.dumps(self._state))

    def _persist(self) -> None:
        """Persist metrics state to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._state, indent=2), encoding="utf-8")
