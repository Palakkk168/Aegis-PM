"""Postgres-backed decision logging."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import asyncpg

from config import get_settings


class DecisionLog:
    """Store and query decision history in Postgres."""

    def __init__(self) -> None:
        """Initialize with lazy pool creation."""
        self.settings = get_settings()
        self._pool: asyncpg.Pool | None = None

    async def initialize(self) -> None:
        """Create the Postgres pool and ensure schema exists."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.settings.postgres_url, min_size=1, max_size=5)
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS decisions (
                    id UUID PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    decision_type TEXT NOT NULL,
                    context TEXT NOT NULL,
                    outcome TEXT NOT NULL
                )
                """
            )

    async def log(self, project_id: str, decision_type: str, context: str, outcome: str) -> dict[str, Any]:
        """Log a decision row."""
        await self.initialize()
        assert self._pool is not None
        record_id = str(uuid4())
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO decisions (id, project_id, decision_type, context, outcome)
                VALUES ($1, $2, $3, $4, $5)
                """,
                record_id,
                project_id,
                decision_type,
                context,
                outcome,
            )
        return {"success": True, "id": record_id}

    async def get_history(self, project_id: str) -> list[dict[str, Any]]:
        """Return all decisions for a project."""
        await self.initialize()
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, project_id, timestamp, decision_type, context, outcome
                FROM decisions
                WHERE project_id = $1
                ORDER BY timestamp ASC
                """,
                project_id,
            )
        return [dict(row) for row in rows]

    async def get_failure_rate(self, task_type: str) -> float:
        """Return the historical failure rate for a task type."""
        await self.initialize()
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM decisions WHERE decision_type = $1",
                task_type,
            )
            failed = await conn.fetchval(
                "SELECT COUNT(*) FROM decisions WHERE decision_type = $1 AND outcome = 'failed'",
                task_type,
            )
        if not total:
            return 0.0
        return float(failed) / float(total)
