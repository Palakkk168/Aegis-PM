"""Shared data models for Aegis PM."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class RunStatus(str, Enum):
    """Execution status for a project run."""

    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    replanning = "replanning"


class TaskStatus(str, Enum):
    """Lifecycle status for a task."""

    pending = "pending"
    ready = "ready"
    in_progress = "in_progress"
    completed = "completed"
    blocked = "blocked"
    failed = "failed"
    skipped = "skipped"


class IntegrationTarget(str, Enum):
    """Supported downstream execution systems."""

    github = "github"
    slack = "slack"
    jira = "jira"
    internal = "internal"


class IntegrationTargets(BaseModel):
    """Optional per-run integration overrides."""

    github_repo_owner: str | None = None
    github_repo_name: str | None = None
    slack_channel: str | None = None
    jira_project_key: str | None = None


class ToolAction(BaseModel):
    """Action to be executed through an integration."""

    target: IntegrationTarget
    operation: str
    params: dict[str, Any] = Field(default_factory=dict)


class TaskFactors(BaseModel):
    """Factors used by the decision engine."""

    impact: float = Field(ge=0.0, le=10.0)
    effort: float = Field(ge=0.0, le=10.0)
    urgency: float = Field(ge=0.0, le=10.0)
    risk: float = Field(ge=0.0, le=10.0)
    dependency_weight: float = Field(ge=0.0, le=10.0)


class TaskNode(BaseModel):
    """A task node in the execution DAG."""

    task_id: str = Field(default_factory=lambda: f"task-{uuid4().hex[:12]}")
    title: str
    description: str
    owner_role: str
    milestone: str
    dependencies: list[str] = Field(default_factory=list)
    factors: TaskFactors
    actions: list[ToolAction] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: TaskStatus = TaskStatus.pending
    score: float = 0.0
    attempts: int = 0
    last_error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class Milestone(BaseModel):
    """A milestone in the structured plan."""

    name: str
    objective: str
    due_day: int
    exit_criteria: list[str]


class ExecutionPlan(BaseModel):
    """Structured execution plan generated from a goal."""

    goal: str
    project_name: str
    deadline_days: int
    strategy: str
    milestones: list[Milestone]
    assumptions: list[str]
    retrieved_context: list[str] = Field(default_factory=list)


class RiskRecord(BaseModel):
    """A detected execution risk."""

    risk_id: str = Field(default_factory=lambda: f"risk-{uuid4().hex[:10]}")
    task_id: str | None = None
    title: str
    description: str
    severity: float = Field(ge=0.0, le=10.0)
    likelihood: float = Field(ge=0.0, le=1.0)
    mitigation: str
    created_at: datetime = Field(default_factory=utc_now)


class DecisionLogEntry(BaseModel):
    """A logged decision made by the orchestrator."""

    decision_id: str = Field(default_factory=lambda: f"decision-{uuid4().hex[:10]}")
    run_id: str
    summary: str
    rationale: str
    related_task_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class GoalRequest(BaseModel):
    """Incoming goal execution request."""

    project_name: str
    goal: str
    integrations: IntegrationTargets = Field(default_factory=IntegrationTargets)


class ExecutionRun(BaseModel):
    """Full state for an execution run."""

    run_id: str = Field(default_factory=lambda: f"run-{uuid4().hex[:12]}")
    project_name: str
    goal: str
    status: RunStatus = RunStatus.pending
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    plan: ExecutionPlan | None = None
    tasks: dict[str, TaskNode] = Field(default_factory=dict)
    completed_task_ids: list[str] = Field(default_factory=list)
    failed_task_ids: list[str] = Field(default_factory=list)
    risk_log: list[RiskRecord] = Field(default_factory=list)
    outputs: list[dict[str, Any]] = Field(default_factory=list)
    report_id: str | None = None


class ReportPayload(BaseModel):
    """Stakeholder report generated after execution."""

    report_id: str = Field(default_factory=lambda: f"report-{uuid4().hex[:12]}")
    run_id: str
    executive_summary: str
    milestone_status: list[dict[str, Any]]
    delivered_tasks: list[dict[str, Any]]
    open_risks: list[dict[str, Any]]
    next_actions: list[str]
    generated_at: datetime = Field(default_factory=utc_now)


class GoalExecutionResult(BaseModel):
    """Return payload for a completed goal execution."""

    run: ExecutionRun
    report: ReportPayload
