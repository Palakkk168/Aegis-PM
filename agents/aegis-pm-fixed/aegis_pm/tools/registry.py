"""Tool registry for dispatching execution actions."""

from __future__ import annotations

from typing import Any

from aegis_pm.schemas import IntegrationTarget, IntegrationTargets, ToolAction
from aegis_pm.tools.github_tool import GitHubTool
from aegis_pm.tools.jira_tool import JiraTool
from aegis_pm.tools.slack_tool import SlackTool


class ToolRegistry:
    """Dispatch tool actions to the correct integration client."""

    def __init__(
        self,
        github: GitHubTool,
        slack: SlackTool,
        jira: JiraTool,
    ) -> None:
        """Create the registry."""
        self.github = github
        self.slack = slack
        self.jira = jira

    async def execute(self, action: ToolAction, overrides: IntegrationTargets) -> dict[str, Any]:
        """Execute a tool action and return the raw integration payload."""
        if action.target == IntegrationTarget.github:
            return await self._execute_github(action, overrides)
        if action.target == IntegrationTarget.slack:
            return await self._execute_slack(action, overrides)
        if action.target == IntegrationTarget.jira:
            return await self._execute_jira(action, overrides)
        return {"status": "internal", "message": action.params.get("message", "No-op internal action")}

    async def _execute_github(self, action: ToolAction, overrides: IntegrationTargets) -> dict[str, Any]:
        """Execute a GitHub action."""
        params = action.params
        if action.operation == "create_issue":
            return await self.github.create_issue(
                title=params["title"],
                body=params["body"],
                owner=overrides.github_repo_owner,
                repo=overrides.github_repo_name,
                labels=params.get("labels"),
            )
        if action.operation == "create_comment":
            return await self.github.create_comment(
                issue_number=int(params["issue_number"]),
                body=params["body"],
                owner=overrides.github_repo_owner,
                repo=overrides.github_repo_name,
            )
        raise ValueError(f"Unsupported GitHub operation: {action.operation}")

    async def _execute_slack(self, action: ToolAction, overrides: IntegrationTargets) -> dict[str, Any]:
        """Execute a Slack action."""
        params = action.params
        if action.operation == "post_message":
            return await self.slack.post_message(
                channel=overrides.slack_channel or params.get("channel"),
                text=params["text"],
            )
        raise ValueError(f"Unsupported Slack operation: {action.operation}")

    async def _execute_jira(self, action: ToolAction, overrides: IntegrationTargets) -> dict[str, Any]:
        """Execute a Jira action."""
        params = action.params
        if action.operation == "create_issue":
            return await self.jira.create_issue(
                summary=params["summary"],
                description=params["description"],
                issue_type=params.get("issue_type", "Task"),
                project_key=overrides.jira_project_key,
            )
        if action.operation == "add_comment":
            return await self.jira.add_comment(
                issue_key=params["issue_key"],
                comment=params["comment"],
            )
        raise ValueError(f"Unsupported Jira operation: {action.operation}")
