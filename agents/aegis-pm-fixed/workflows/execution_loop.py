"""Execution loop for the PM orchestrator."""

from __future__ import annotations

import asyncio

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from agents.pm_agent import PMAAgent
from agents.planner_agent import PlannerAgent
from agents.reporter_agent import ReporterAgent
from agents.risk_agent import RiskAgent
from agents.task_agent import TaskAgent
from config import get_settings
from core.schemas import Goal, ProjectState, ProjectStatus, Report
from memory.decision_log import DecisionLog
from memory.state_store import StateStore
from tools.base_tool import configure_tool_context
from tools.memory_tools import set_project_context


class ExecutionLoop:
    """Orchestrates the full project execution lifecycle."""

    def __init__(self) -> None:
        """Initialize all agents and backing services."""
        settings = get_settings()
        configure_tool_context(settings)

        self.decision_log = DecisionLog()
        self.state_store = StateStore()

        planner = PlannerAgent()
        task_agent = TaskAgent()
        risk_agent = RiskAgent(decision_log=self.decision_log)
        reporter = ReporterAgent(decision_log=self.decision_log)

        self.pm_agent = PMAAgent(
            planner=planner,
            task_agent=task_agent,
            risk_agent=risk_agent,
            reporter=reporter,
        )

        self._session_service = InMemorySessionService()
        self._runner = Runner(
            agent=self.pm_agent,
            app_name=settings.app_name,
            session_service=self._session_service,
        )

    async def run(self, goal: Goal) -> Report:
        """Execute a project goal end-to-end."""
        set_project_context(goal.project_id)

        state = ProjectState(goal=goal, status=ProjectStatus.RUNNING)
        await self.state_store.save_state(goal.project_id, state)

        # Generate plan
        plan = await self.pm_agent._planner.generate_plan(
            self._runner, goal, []
        )

        # Generate task graph
        task_graph = await self.pm_agent._task_agent.generate_task_graph(
            self._runner,
            goal.raw_input,
            plan.milestones,
            user_id=goal.user_id,
            session_id=goal.project_id,
        )
        plan.task_graph = task_graph
        state.plan = plan
        await self.state_store.save_state(goal.project_id, state)

        # Analyze risk
        risk_report = await self.pm_agent._risk_agent.analyze(self._runner, state)

        # Generate report
        settings = get_settings()
        report = await self.pm_agent._reporter.generate_report(
            self._runner, state, slack_channel=settings.slack_bot_token and "#general" or None
        )

        state.status = ProjectStatus.COMPLETED
        state.latest_report = report.model_dump(mode="json")
        await self.state_store.save_state(goal.project_id, state)

        return report

    async def get_state(self, project_id: str) -> ProjectState | None:
        """Load project state from Redis."""
        return await self.state_store.load_state(project_id)

    async def pause(self, project_id: str) -> ProjectState | None:
        """Pause a running project."""
        return await self.state_store.set_paused(project_id, True)

    async def resume(self, project_id: str) -> ProjectState | None:
        """Resume a paused project."""
        return await self.state_store.set_paused(project_id, False)
