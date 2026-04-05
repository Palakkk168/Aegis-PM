"""Persistent decision log storage."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from aegis_pm.schemas import DecisionLogEntry


class DecisionLog:
    """Append-only decision log for execution auditing."""

    def __init__(self, path: Path) -> None:
        """Initialize the decision log."""
        self.path = path
        self._lock = asyncio.Lock()
        if not self.path.exists():
            self._persist([])

    async def append(self, entry: DecisionLogEntry) -> None:
        """Store a decision log entry."""
        async with self._lock:
            payload = self._load()
            payload.append(entry.model_dump(mode="json"))
            self._persist(payload)

    async def list_for_run(self, run_id: str) -> list[DecisionLogEntry]:
        """Return all decisions for a run."""
        async with self._lock:
            payload = self._load()
            return [
                DecisionLogEntry.model_validate(item)
                for item in payload
                if item["run_id"] == run_id
            ]

    def _load(self) -> list[dict]:
        """Read the decision log payload."""
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _persist(self, payload: list[dict]) -> None:
        """Write the decision log payload."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
