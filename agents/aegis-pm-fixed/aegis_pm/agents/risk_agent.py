"""Risk prediction and mitigation analysis."""

from __future__ import annotations

from aegis_pm.agents.base import BaseAgent
from aegis_pm.schemas import ExecutionRun, RiskRecord, TaskNode, TaskStatus


class RiskAgent(BaseAgent):
    """Predict risks before execution failure cascades."""

    def __init__(self) -> None:
        """Create the risk agent."""
        super().__init__("risk")

    async def analyze(self, run: ExecutionRun, historical_context: list[dict]) -> list[RiskRecord]:
        """Analyze the run state and return predicted or observed risks."""
        risks: list[RiskRecord] = []
        historical_failures = sum(
            1 for item in historical_context if item.get("metadata", {}).get("outcome") == "failed"
        )
        for task in run.tasks.values():
            severity = self._compute_severity(task, historical_failures)
            if task.status == TaskStatus.failed:
                risks.append(
                    RiskRecord(
                        task_id=task.task_id,
                        title="Task execution failed",
                        description=f"Task '{task.title}' failed and may block downstream work.",
                        severity=severity,
                        likelihood=1.0,
                        mitigation="Create a mitigation task, notify stakeholders, and reroute downstream dependencies.",
                    )
                )
                continue
            if task.status in {TaskStatus.pending, TaskStatus.ready} and severity >= 7.5:
                risks.append(
                    RiskRecord(
                        task_id=task.task_id,
                        title="High-risk task detected",
                        description=f"Task '{task.title}' has elevated execution risk before start.",
                        severity=severity,
                        likelihood=min(0.95, severity / 10),
                        mitigation="Add an earlier alignment checkpoint and ensure dependency owners are engaged.",
                    )
                )
        return risks

    def _compute_severity(self, task: TaskNode, historical_failures: int) -> float:
        """Compute risk severity from task complexity and history."""
        dependency_pressure = min(len(task.dependencies) * 1.5, 4.0)
        historical_pressure = min(historical_failures * 0.5, 3.0)
        severity = task.factors.risk * 0.5 + task.factors.effort * 0.2 + dependency_pressure + historical_pressure
        return round(min(severity, 10.0), 2)
