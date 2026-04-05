"""Jira integration client."""

from __future__ import annotations

import base64

from aegis_pm.tools.base import BaseIntegrationClient, IntegrationError


class JiraTool(BaseIntegrationClient):
    """Execute real Jira issue operations."""

    def __init__(
        self,
        base_url: str | None,
        email: str | None,
        api_token: str | None,
        project_key: str | None,
    ) -> None:
        """Initialize the Jira client."""
        self.email = email
        self.api_token = api_token
        self.project_key = project_key
        auth_header = ""
        if email and api_token:
            token = base64.b64encode(f"{email}:{api_token}".encode("utf-8")).decode("utf-8")
            auth_header = f"Basic {token}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if auth_header:
            headers["Authorization"] = auth_header
        super().__init__(f"{base_url.rstrip('/')}/rest/api/3" if base_url else "", headers=headers)

    def _require_project(self, project_key: str | None) -> str:
        """Resolve a Jira project key or fail loudly."""
        resolved = project_key or self.project_key
        if not self.base_url or not self.email or not self.api_token or not resolved:
            raise IntegrationError("Jira credentials or project key are missing")
        return resolved

    async def create_issue(
        self,
        summary: str,
        description: str,
        *,
        issue_type: str = "Task",
        project_key: str | None = None,
    ) -> dict:
        """Create a Jira issue."""
        resolved_project = self._require_project(project_key)
        return await self.request(
            "POST",
            "/issue",
            json_payload={
                "fields": {
                    "project": {"key": resolved_project},
                    "summary": summary,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": description}],
                            }
                        ],
                    },
                    "issuetype": {"name": issue_type},
                }
            },
        )

    async def add_comment(self, issue_key: str, comment: str) -> dict:
        """Add a comment to an existing Jira issue."""
        self._require_project(None)
        return await self.request(
            "POST",
            f"/issue/{issue_key}/comment",
            json_payload={
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": comment}],
                        }
                    ],
                }
            },
        )
