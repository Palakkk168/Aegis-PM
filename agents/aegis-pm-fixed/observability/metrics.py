"""In-memory metrics registry."""

from __future__ import annotations

import asyncio


class MetricsRegistry:
    """Track process metrics exposed by the API."""

    def __init__(self) -> None:
        """Initialize empty metrics."""
        self._lock = asyncio.Lock()
        self._metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "replan_count": 0,
            "avg_task_latency_ms": 0.0,
            "risk_detections": 0,
            "llm_calls_total": 0,
            "request_count": 0,
        }
        self._latency_total = 0.0
        self._latency_count = 0

    async def increment(self, name: str, amount: int = 1) -> None:
        """Increment a counter metric."""
        async with self._lock:
            self._metrics[name] = self._metrics.get(name, 0) + amount

    async def observe_task_latency(self, latency_ms: float) -> None:
        """Track task latency and update the rolling average."""
        async with self._lock:
            self._latency_total += latency_ms
            self._latency_count += 1
            self._metrics["avg_task_latency_ms"] = round(self._latency_total / self._latency_count, 3)

    async def snapshot(self) -> dict[str, float | int]:
        """Return a copy of the current metrics."""
        async with self._lock:
            return dict(self._metrics)


metrics_registry = MetricsRegistry()
