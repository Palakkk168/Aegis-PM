"""Decision scoring for ready-to-run tasks."""

from __future__ import annotations

from aegis_pm.schemas import TaskNode


def score_task(task: TaskNode, downstream_unlock_count: int, historical_failure_rate: float) -> float:
    """Compute a composite task priority score."""
    factors = task.factors
    impact_score = factors.impact * 0.30
    urgency_score = factors.urgency * 0.25
    risk_score = factors.risk * 0.15
    dependency_score = min(downstream_unlock_count, 5) * 0.10 + factors.dependency_weight * 0.10
    effort_penalty = factors.effort * 0.15
    failure_penalty = historical_failure_rate * 10 * 0.15
    return round(impact_score + urgency_score + risk_score + dependency_score - effort_penalty - failure_penalty, 3)
