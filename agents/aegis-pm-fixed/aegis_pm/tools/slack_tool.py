"""Slack integration client."""

from __future__ import annotations

from aegis_pm.tools.base import BaseIntegrationClient, IntegrationError


class SlackTool(BaseIntegrationClient):
    """Execute real Slack messaging operations."""

    def __init__(self, bot_token: str | None, default_channel: str | None) -> None:
        """Initialize the Slack client."""
        self.bot_token = bot_token
        self.default_channel = default_channel
        headers = {}
        if bot_token:
            headers["Authorization"] = f"Bearer {bot_token}"
        super().__init__("https://slack.com/api", headers=headers)

    def _require_channel(self, channel: str | None) -> str:
        """Resolve the Slack channel or fail loudly."""
        resolved = channel or self.default_channel
        if not self.bot_token or not resolved:
            raise IntegrationError("Slack credentials or channel are missing")
        return resolved

    async def post_message(self, channel: str | None, text: str) -> dict:
        """Post a message to Slack."""
        resolved_channel = self._require_channel(channel)
        payload = await self.request(
            "POST",
            "/chat.postMessage",
            headers={"Content-Type": "application/json; charset=utf-8"},
            json_payload={"channel": resolved_channel, "text": text},
        )
        if not payload.get("ok", False):
            raise IntegrationError(f"Slack post_message failed: {payload}")
        return payload
