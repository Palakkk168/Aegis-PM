"""Decision scoring for task prioritization."""

from __future__ import annotations

from core.schemas import Task


def score_task(task: Task) -> float:
    """Compute the weighted priority score for a task."""
    return (
        (task.impact * 0.35)
        + (task.urgency * 0.25)
        + ((1 - task.effort) * 0.20)
        + ((1 - task.risk_score) * 0.20)
    )


def prioritize(tasks: list[Task]) -> list[Task]:
    """Sort tasks by priority descending."""
    return sorted(tasks, key=score_task, reverse=True)
