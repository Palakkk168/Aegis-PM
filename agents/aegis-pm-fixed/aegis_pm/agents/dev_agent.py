"""Development execution agent."""

from __future__ import annotations

from aegis_pm.agents.base import BaseAgent
from aegis_pm.schemas import IntegrationTargets, TaskNode
from aegis_pm.tools.registry import ToolRegistry


class DevAgent(BaseAgent):
    """Execute development-oriented work via downstream tools."""

    def __init__(self) -> None:
        """Create the development agent."""
        super().__init__("dev")

    async def execute(self, task: TaskNode, tools: ToolRegistry, overrides: IntegrationTargets) -> list[dict]:
        """Execute task actions and return integration outputs."""
        outputs = []
        for action in task.actions:
            outputs.append(await tools.execute(action, overrides))
        return outputs
