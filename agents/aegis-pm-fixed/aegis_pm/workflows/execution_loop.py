"""Execution loop wrapper for the PM orchestrator."""

from __future__ import annotations

from aegis_pm.agents.pm_agent import PMAgent
from aegis_pm.schemas import GoalExecutionResult, GoalRequest


class ExecutionLoop:
    """Thin workflow wrapper around the PM orchestrator."""

    def __init__(self, pm_agent: PMAgent) -> None:
        """Store the orchestrator instance."""
        self.pm_agent = pm_agent

    async def run(self, request: GoalRequest) -> GoalExecutionResult:
        """Run the strict PM execution flow."""
        return await self.pm_agent.run(request)
