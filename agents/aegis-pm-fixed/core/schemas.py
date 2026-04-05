"""Shared Pydantic schemas for Aegis PM."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


class TaskStatus(str, Enum):
    """Execution status for an individual task."""

    PENDING = "PENDING"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class ProjectStatus(str, Enum):
    """Execution status for the overall project."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"


class Goal(BaseModel):
    """Raw goal submission for a new project."""

    project_id: str = Field(default_factory=lambda: f"project-{uuid4().hex[:12]}")
    user_id: str
    raw_input: str
    deadline: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class Milestone(BaseModel):
    """Milestone output from the planning system."""

    id: str = Field(default_factory=lambda: f"milestone-{uuid4().hex[:10]}")
    name: str
    description: str
    deadline: datetime
    task_ids: list[str] = Field(default_factory=list)


class Task(BaseModel):
    """Atomic executable task in the project DAG."""

    id: str = Field(default_factory=lambda: f"task-{uuid4().hex[:10]}")
    name: str
    description: str
    dependencies: list[str] = Field(default_factory=list)
    impact: float = Field(ge=0.0, le=1.0)
    effort: float = Field(ge=0.0, le=1.0)
    urgency: float = Field(ge=0.0, le=1.0)
    risk_score: float = Field(ge=0.0, le=1.0)
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: str
    tool_payload: dict[str, Any] = Field(default_factory=dict)


class TaskGraph(BaseModel):
    """Graph wrapper around a NetworkX DiGraph and task map."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    graph: nx.DiGraph = Field(default_factory=nx.DiGraph)
    tasks: dict[str, Task] = Field(default_factory=dict)


class Plan(BaseModel):
    """Structured plan produced by the planner and task agents."""

    milestones: list[Milestone]
    task_graph: TaskGraph
    created_at: datetime = Field(default_factory=utc_now)


class RiskItem(BaseModel):
    """Per-task risk score and mitigation guidance."""

    task_id: str
    risk_score: float = Field(ge=0.0, le=1.0)
    reason: str
    mitigation: str


class RiskReport(BaseModel):
    """Aggregated risk assessment for the current project state."""

    items: list[RiskItem]
    overall_risk: float = Field(ge=0.0, le=1.0)


class ExecutionResult(BaseModel):
    """Outcome of executing a single task."""

    task_id: str
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    duration_ms: float


class ProjectState(BaseModel):
    """Structured project state stored in Redis."""

    goal: Goal
    plan: Plan | None = None
    completed: list[str] = Field(default_factory=list)
    failed: list[str] = Field(default_factory=list)
    replan_count: int = 0
    replan_budget: int = 3
    status: ProjectStatus = ProjectStatus.PENDING
    updated_at: datetime = Field(default_factory=utc_now)
    paused: bool = False
    latest_report: dict[str, Any] | None = None


class Report(BaseModel):
    """Stakeholder-facing execution report."""

    summary: str
    completion_pct: float = Field(ge=0.0, le=100.0)
    blocked_tasks: list[str]
    top_risks: list[RiskItem]
    decisions: list[dict[str, Any]]
    next_actions: list[str]
