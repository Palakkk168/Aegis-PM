"""Stakeholder reporting agent."""

from __future__ import annotations

from collections import Counter

from aegis_pm.agents.base import BaseAgent
from aegis_pm.schemas import ExecutionRun, ReportPayload, RiskRecord, TaskStatus


class ReporterAgent(BaseAgent):
    """Generate stakeholder-facing reports from execution state."""

    def __init__(self) -> None:
        """Create the reporting agent."""
        super().__init__("reporter")

    async def generate_report(self, run: ExecutionRun) -> ReportPayload:
        """Generate a concise stakeholder report."""
        milestone_counts = Counter(task.milestone for task in run.tasks.values())
        completed_counts = Counter(
            task.milestone for task in run.tasks.values() if task.status == TaskStatus.completed
        )
        milestone_status = [
            {
                "milestone": milestone,
                "completed": completed_counts.get(milestone, 0),
                "total": total,
            }
            for milestone, total in milestone_counts.items()
        ]
        delivered_tasks = [
            {
                "task_id": task.task_id,
                "title": task.title,
                "owner_role": task.owner_role,
                "status": task.status,
                "score": task.score,
            }
            for task in run.tasks.values()
            if task.status == TaskStatus.completed
        ]
        open_risks = [risk.model_dump(mode="json") for risk in run.risk_log if risk.severity >= 6.0]
        next_actions = self._next_actions(run.risk_log)
        summary = (
            f"Project '{run.project_name}' finished with {len(delivered_tasks)} completed tasks, "
            f"{len(run.failed_task_ids)} failed tasks, and {len(open_risks)} material risks."
        )
        return ReportPayload(
            run_id=run.run_id,
            executive_summary=summary,
            milestone_status=milestone_status,
            delivered_tasks=delivered_tasks,
            open_risks=open_risks,
            next_actions=next_actions,
        )

    def _next_actions(self, risks: list[RiskRecord]) -> list[str]:
        """Generate next actions from the remaining risk log."""
        if not risks:
            return ["Continue with the next milestone wave using the current operating cadence."]
        actions = []
        for risk in risks[:3]:
            actions.append(f"{risk.title}: {risk.mitigation}")
        return actions
