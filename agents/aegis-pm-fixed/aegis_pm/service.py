"""Service construction for Aegis PM."""

from __future__ import annotations

from aegis_pm.agents.dev_agent import DevAgent
from aegis_pm.agents.planner_agent import PlannerAgent
from aegis_pm.agents.pm_agent import PMAgent
from aegis_pm.agents.qa_agent import QAAgent
from aegis_pm.agents.reporter_agent import ReporterAgent
from aegis_pm.agents.risk_agent import RiskAgent
from aegis_pm.agents.task_agent import TaskAgent
from aegis_pm.config import get_settings
from aegis_pm.memory.decision_log import DecisionLog
from aegis_pm.memory.state_store import StateStore
from aegis_pm.memory.vector_store import VectorStore
from aegis_pm.observability.metrics import MetricsRegistry
from aegis_pm.tools.github_tool import GitHubTool
from aegis_pm.tools.jira_tool import JiraTool
from aegis_pm.tools.registry import ToolRegistry
from aegis_pm.tools.slack_tool import SlackTool


def build_pm_service() -> PMAgent:
    """Construct the PM service with all dependencies."""
    settings = get_settings()
    github = GitHubTool(
        token=settings.github_token,
        owner=settings.github_repo_owner,
        repo=settings.github_repo_name,
    )
    slack = SlackTool(
        bot_token=settings.slack_bot_token,
        default_channel=settings.slack_default_channel,
    )
    jira = JiraTool(
        base_url=settings.jira_base_url,
        email=settings.jira_user_email,
        api_token=settings.jira_api_token,
        project_key=settings.jira_project_key,
    )
    tools = ToolRegistry(github=github, slack=slack, jira=jira)
    return PMAgent(
        planner=PlannerAgent(),
        task_agent=TaskAgent(),
        risk_agent=RiskAgent(),
        dev_agent=DevAgent(),
        qa_agent=QAAgent(),
        reporter=ReporterAgent(),
        tools=tools,
        state_store=StateStore(settings.data_dir / "state.json"),
        vector_store=VectorStore(settings.data_dir / "memory.json"),
        decision_log=DecisionLog(settings.data_dir / "decisions.json"),
        metrics=MetricsRegistry(settings.data_dir / "metrics.json"),
        max_parallel_tasks=settings.max_parallel_tasks,
    )
