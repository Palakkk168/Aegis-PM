"""Slack ADK tools."""

from __future__ import annotations

import json

from google.adk.tools import FunctionTool

from tools.base_tool import request_json, tool_context


async def send_slack_message(channel: str, text: str) -> dict:
    """Sends a message to a Slack channel."""
    if tool_context is None:
        return {"success": False, "error": "tool context not configured"}
    headers = {
        "Authorization": f"Bearer {tool_context.settings.slack_bot_token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    result = await request_json(
        "POST",
        "https://slack.com/api/chat.postMessage",
        headers=headers,
        json_payload={"channel": channel, "text": text},
    )
    if not result["success"]:
        return result
    data = result["data"]
    return {"success": bool(data.get("ok")), "channel": data.get("channel"), "ts": data.get("ts"), "error": data.get("error")}


async def send_slack_report(channel: str, report_json: str) -> dict:
    """Sends a formatted project report to a Slack channel."""
    parsed = json.loads(report_json)
    summary = parsed.get("summary", "Aegis PM report")
    next_actions = "\n".join(f"- {item}" for item in parsed.get("next_actions", []))
    text = f"{summary}\n\nNext actions:\n{next_actions or '- none'}"
    return await send_slack_message(channel=channel, text=text)


send_slack_message_tool = FunctionTool(func=send_slack_message)
send_slack_report_tool = FunctionTool(func=send_slack_report)
