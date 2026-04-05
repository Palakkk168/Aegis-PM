"""GitHub integration client."""

from __future__ import annotations

from aegis_pm.tools.base import BaseIntegrationClient, IntegrationError


class GitHubTool(BaseIntegrationClient):
    """Execute real GitHub issue operations."""

    def __init__(self, token: str | None, owner: str | None, repo: str | None) -> None:
        """Initialize the GitHub client."""
        self.token = token
        self.owner = owner
        self.repo = repo
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        super().__init__("https://api.github.com", headers=headers)

    def _require_repo(self, owner: str | None, repo: str | None) -> tuple[str, str]:
        """Resolve repository coordinates or fail loudly."""
        resolved_owner = owner or self.owner
        resolved_repo = repo or self.repo
        if not self.token or not resolved_owner or not resolved_repo:
            raise IntegrationError("GitHub credentials or repository details are missing")
        return resolved_owner, resolved_repo

    async def create_issue(
        self,
        title: str,
        body: str,
        *,
        owner: str | None = None,
        repo: str | None = None,
        labels: list[str] | None = None,
    ) -> dict:
        """Create a GitHub issue."""
        resolved_owner, resolved_repo = self._require_repo(owner, repo)
        return await self.request(
            "POST",
            f"/repos/{resolved_owner}/{resolved_repo}/issues",
            json_payload={
                "title": title,
                "body": body,
                "labels": labels or [],
            },
        )

    async def create_comment(
        self,
        issue_number: int,
        body: str,
        *,
        owner: str | None = None,
        repo: str | None = None,
    ) -> dict:
        """Create a comment on an existing issue."""
        resolved_owner, resolved_repo = self._require_repo(owner, repo)
        return await self.request(
            "POST",
            f"/repos/{resolved_owner}/{resolved_repo}/issues/{issue_number}/comments",
            json_payload={"body": body},
        )
