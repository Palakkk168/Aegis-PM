"""Shared helpers for Aegis PM integration tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from config import Settings
from observability.logger import configure_logging


logger = configure_logging()


@dataclass
class ToolContext:
    """Shared context for real integration tools."""

    settings: Settings


tool_context: ToolContext | None = None


def configure_tool_context(settings: Settings) -> None:
    """Configure global tool context."""
    global tool_context
    tool_context = ToolContext(settings=settings)


async def request_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute an async HTTP request and return a normalized dict."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method=method, url=url, headers=headers, json=json_payload)
            data = response.json() if response.text else {}
            if response.status_code >= 400:
                return {"success": False, "status_code": response.status_code, "error": data or response.text}
            return {"success": True, "status_code": response.status_code, "data": data}
    except httpx.HTTPError as exc:
        logger.error("tool.http_error", method=method, url=url, error=str(exc))
        return {"success": False, "error": str(exc)}
