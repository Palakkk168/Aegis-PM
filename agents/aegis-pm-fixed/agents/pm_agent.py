"""Root PM ADK agent."""

from __future__ import annotations

from typing import Any

from agents.base_agent import BaseAegisAgent
from tools.github_tool import create_github_branch_tool, create_github_issue_tool
from tools.jira_tool import create_jira_ticket_tool
from tools.memory_tools import log_decision_tool, retrieve_context_tool, store_context_tool
from tools.slack_tool import send_slack_message_tool


class PMAAgent(BaseAegisAgent):
    """Autonomous AI project manager root agent."""

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, planner, task_agent, risk_agent, reporter, **kwargs: Any) -> None:
        """Initialize the root PM agent with sub-agents and core tools."""
        super().__init__(
            name="pm_agent",
            model="gemini-2.0-flash",
            description="Autonomous AI Project Manager",
            instruction=(
                "You are Aegis PM, an autonomous project manager.\n"
                "When given a goal:\n"
                "1. Delegate to planner_agent to generate a plan\n"
                "2. Delegate to task_agent to decompose into tasks\n"
                "3. Execute tasks using available tools\n"
                "4. Continuously delegate to risk_agent to monitor risks\n"
                "5. If risk > 0.7, delegate back to planner_agent to replan\n"
                "6. Delegate to reporter_agent for status updates\n"
                "Always think before acting. Log every major decision."
            ),
            tools=[
                create_github_issue_tool,
                create_github_branch_tool,
                send_slack_message_tool,
                create_jira_ticket_tool,
                store_context_tool,
                retrieve_context_tool,
                log_decision_tool,
            ],
            sub_agents=[planner, task_agent, risk_agent, reporter],
            **kwargs,
        )
        object.__setattr__(self, "_planner", planner)
        object.__setattr__(self, "_task_agent", task_agent)
        object.__setattr__(self, "_risk_agent", risk_agent)
        object.__setattr__(self, "_reporter", reporter)
