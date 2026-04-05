"""Quality assurance execution agent."""

from __future__ import annotations

from aegis_pm.agents.base import BaseAgent
from aegis_pm.schemas import IntegrationTargets, TaskNode
from aegis_pm.tools.registry import ToolRegistry


class QAAgent(BaseAgent):
    """Execute QA-oriented work via downstream tools."""

    def __init__(self) -> None:
        """Create the QA agent."""
        super().__init__("qa")

    async def execute(self, task: TaskNode, tools: ToolRegistry, overrides: IntegrationTargets) -> list[dict]:
        """Execute QA task actions."""
        outputs = []
        for action in task.actions:
            outputs.append(await tools.execute(action, overrides))
        return outputs
