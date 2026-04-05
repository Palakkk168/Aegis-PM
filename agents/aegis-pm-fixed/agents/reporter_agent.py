"""Reporter ADK agent."""

from __future__ import annotations

import json
from typing import Any

from google.adk.runners import Runner

from agents.base_agent import BaseAegisAgent
from core.schemas import ProjectState, Report, TaskStatus
from memory.decision_log import DecisionLog
from tools.memory_tools import retrieve_context_tool
from tools.slack_tool import send_slack_report


class ReporterAgent(BaseAegisAgent):
    """Generates stakeholder-facing reports."""

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, decision_log: DecisionLog, **kwargs: Any) -> None:
        """Initialize the reporter agent."""
        super().__init__(
            name="reporter_agent",
            model="gemini-2.0-flash",
            description="Generates human-readable project reports",
            instruction="You are a reporting agent. Produce concise, executive-readable project reports.",
            tools=[retrieve_context_tool],
            **kwargs,
        )
        object.__setattr__(self, "_decision_log", decision_log)

    async def generate_report(self, runner: Runner, state: ProjectState, slack_channel: str | None = None) -> Report:
        """Generate a report and optionally send it to Slack."""
        _ = runner
        tasks = list(state.plan.task_graph.tasks.values()) if state.plan else []
        completed = sum(task.status == TaskStatus.COMPLETE for task in tasks)
        completion_pct = round((completed / max(len(tasks), 1)) * 100, 2)
        decisions = await self._decision_log.get_history(state.goal.project_id)
        blocked = [task.id for task in tasks if task.status == TaskStatus.FAILED]
        summary = f"{state.goal.raw_input}: {completed}/{len(tasks)} tasks completed with status {state.status}."
        report = Report(
            summary=summary,
            completion_pct=completion_pct,
            blocked_tasks=blocked,
            top_risks=[],
            decisions=decisions[-10:],
            next_actions=["Clear blocked tasks", "Validate release readiness", "Review next milestone scope"],
        )
        if slack_channel:
            await send_slack_report(channel=slack_channel, report_json=json.dumps(report.model_dump(mode="json")))
        return report
