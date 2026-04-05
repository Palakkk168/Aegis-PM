"""FastAPI interface layer for Aegis PM."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from aegis_pm.schemas import GoalRequest
from aegis_pm.service import build_pm_service


def build_app() -> FastAPI:
    """Create the FastAPI application."""
    app = FastAPI(title="Aegis PM", version="0.1.0")
    service = build_pm_service()

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Return service health."""
        return {"status": "ok"}

    @app.post("/goals/execute")
    async def execute_goal(request: GoalRequest) -> dict:
        """Execute a goal end-to-end."""
        result = await service.run(request)
        return result.model_dump(mode="json")

    @app.get("/runs/{run_id}")
    async def get_run(run_id: str) -> dict:
        """Return persisted run state."""
        run = await service.state_store.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        return run.model_dump(mode="json")

    @app.get("/reports/{run_id}")
    async def get_report(run_id: str) -> dict:
        """Return a persisted report."""
        report = await service.state_store.get_report(run_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return report.model_dump(mode="json")

    @app.get("/metrics")
    async def get_metrics() -> dict:
        """Return current metrics."""
        return await service.metrics.snapshot()

    return app
