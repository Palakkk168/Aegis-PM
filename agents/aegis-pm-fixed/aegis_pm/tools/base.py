"""Base utilities for real integration clients."""

from __future__ import annotations

from typing import Any

import httpx

from aegis_pm.workflows.retry_manager import with_retry


class IntegrationError(RuntimeError):
    """Raised when an integration call cannot be completed."""


class BaseIntegrationClient:
    """Shared async HTTP integration client."""

    def __init__(self, base_url: str, headers: dict[str, str] | None = None) -> None:
        """Store common client configuration."""
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}

    async def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        json_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an HTTP request with retries."""

        async def _perform() -> dict[str, Any]:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.request(
                    method=method,
                    url=f"{self.base_url}{path}",
                    headers={**self.headers, **(headers or {})},
                    json=json_payload,
                )
                if response.status_code >= 400:
                    raise IntegrationError(
                        f"{method} {path} failed with {response.status_code}: {response.text}"
                    )
                if not response.text.strip():
                    return {}
                return response.json()

        return await with_retry(_perform)
