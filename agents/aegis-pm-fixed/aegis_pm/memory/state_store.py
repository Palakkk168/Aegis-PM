"""Persistent execution state storage."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from aegis_pm.schemas import ExecutionRun, ReportPayload


class StateStore:
    """Persist runs and reports to local JSON storage."""

    def __init__(self, path: Path) -> None:
        """Initialize the store with a storage path."""
        self.path = path
        self._lock = asyncio.Lock()
        if not self.path.exists():
            self._persist({"runs": {}, "reports": {}})

    async def save_run(self, run: ExecutionRun) -> None:
        """Persist a run record."""
        async with self._lock:
            payload = self._load()
            payload["runs"][run.run_id] = run.model_dump(mode="json")
            self._persist(payload)

    async def get_run(self, run_id: str) -> ExecutionRun | None:
        """Load a run record by identifier."""
        async with self._lock:
            payload = self._load()
            data = payload["runs"].get(run_id)
            return ExecutionRun.model_validate(data) if data else None

    async def list_runs(self) -> list[ExecutionRun]:
        """Return all persisted runs."""
        async with self._lock:
            payload = self._load()
            return [ExecutionRun.model_validate(item) for item in payload["runs"].values()]

    async def save_report(self, report: ReportPayload) -> None:
        """Persist a generated report."""
        async with self._lock:
            payload = self._load()
            payload["reports"][report.run_id] = report.model_dump(mode="json")
            self._persist(payload)

    async def get_report(self, run_id: str) -> ReportPayload | None:
        """Load a report by run identifier."""
        async with self._lock:
            payload = self._load()
            data = payload["reports"].get(run_id)
            return ReportPayload.model_validate(data) if data else None

    def _load(self) -> dict:
        """Read the JSON payload from disk."""
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _persist(self, payload: dict) -> None:
        """Write the JSON payload to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
