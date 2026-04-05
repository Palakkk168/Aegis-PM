"""Risk analysis ADK agent."""

from __future__ import annotations

from typing import Any

from google.adk.runners import Runner

from agents.base_agent import BaseAegisAgent
from core.schemas import ProjectState, RiskItem, RiskReport, TaskStatus
from memory.decision_log import DecisionLog
from tools.memory_tools import log_decision_tool, retrieve_context_tool


class RiskAgent(BaseAegisAgent):
    """Analyzes project state and scores risk per task."""

    model_config = {"arbitrary_types_allowed": True}

    _decision_log: Any = None

    def __init__(self, decision_log: DecisionLog, **kwargs: Any) -> None:
        """Initialize the risk agent."""
        super().__init__(
            name="risk_agent",
            model="gemini-2.0-flash",
            description="Analyzes project state and scores risk per task",
            instruction=(
                "You are a risk analysis agent. Analyze the project state and identify risk per task. "
                "Use the exact risk formula provided by the system."
            ),
            tools=[retrieve_context_tool, log_decision_tool],
            **kwargs,
        )
        object.__setattr__(self, "_decision_log", decision_log)

    async def analyze(self, runner: Runner, state: ProjectState) -> RiskReport:
        """Calculate deterministic risk and optionally enrich through ADK context."""
        _ = runner
        items: list[RiskItem] = []
        if state.plan is None:
            return RiskReport(items=[], overall_risk=0.0)
        total_risk = 0.0
        task_count = len(state.plan.task_graph.tasks)
        for task in state.plan.task_graph.tasks.values():
            if task.status == TaskStatus.COMPLETE:
                continue
            dep_count_normalized = min(len(task.dependencies) / max(task_count, 1), 1.0)
            historical_failure_rate = await self._decision_log.get_failure_rate(task.assigned_agent)
            risk_score = min((task.effort * 0.4) + (dep_count_normalized * 0.3) + (historical_failure_rate * 0.3), 1.0)
            if risk_score >= 0.4:
                items.append(
                    RiskItem(
                        task_id=task.id,
                        risk_score=risk_score,
                        reason=f"Complexity={task.effort}, dependency load={dep_count_normalized}, history={historical_failure_rate}",
                        mitigation="Break work down further, assign a checkpoint, and reduce dependency uncertainty.",
                    )
                )
            total_risk += risk_score
        overall = round(total_risk / max(task_count, 1), 4)
        return RiskReport(items=items, overall_risk=overall)
