"""FastAPI routes for Aegis PM."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.schemas import Goal
from observability.metrics import metrics_registry
from workflows.execution_loop import ExecutionLoop


router = APIRouter()
execution_loop = ExecutionLoop()


class ProjectCreateRequest(BaseModel):
    """Payload for creating a new project run."""

    user_id: str
    goal: str
    deadline_days: int = Field(default=30, ge=1, le=365)
    metadata: dict = Field(default_factory=dict)


@router.post("/projects")
async def create_project(request: ProjectCreateRequest) -> dict:
    """Submit a goal and start project execution."""
    goal = Goal(
        user_id=request.user_id,
        raw_input=request.goal,
        deadline=datetime.now(UTC) + timedelta(days=request.deadline_days),
        metadata=request.metadata,
    )
    report = await execution_loop.run(goal)
    return {"project_id": goal.project_id, "report": report.model_dump(mode="json")}


@router.get("/projects/{project_id}")
async def get_project(project_id: str) -> dict:
    """Return current project state."""
    state = await execution_loop.get_state(project_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return state.model_dump(mode="json")


@router.get("/projects/{project_id}/report")
async def get_project_report(project_id: str) -> dict:
    """Return the latest report for a project."""
    state = await execution_loop.get_state(project_id)
    if state is None or state.latest_report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return state.latest_report


@router.post("/projects/{project_id}/pause")
async def pause_project(project_id: str) -> dict:
    """Pause project execution."""
    state = await execution_loop.pause(project_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return state.model_dump(mode="json")


@router.post("/projects/{project_id}/resume")
async def resume_project(project_id: str) -> dict:
    """Resume project execution."""
    state = await execution_loop.resume(project_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return state.model_dump(mode="json")


@router.get("/metrics")
async def get_metrics() -> dict:
    """Return current process metrics."""
    return await metrics_registry.snapshot()


@router.get("/health")
async def health() -> dict:
    """Return service health status."""
    return {"status": "ok"}
