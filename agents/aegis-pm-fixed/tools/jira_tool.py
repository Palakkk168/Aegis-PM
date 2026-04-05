"""Jira ADK tools."""

from __future__ import annotations

import base64

from google.adk.tools import FunctionTool

from tools.base_tool import request_json, tool_context


def _jira_headers() -> dict[str, str]:
    """Build Jira auth headers."""
    assert tool_context is not None
    token = base64.b64encode(
        f"{tool_context.settings.jira_email}:{tool_context.settings.jira_api_token}".encode("utf-8")
    ).decode("utf-8")
    return {
        "Authorization": f"Basic {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


async def create_jira_ticket(project_key: str, summary: str, description: str, issue_type: str, priority: str) -> dict:
    """Creates a new Jira ticket in the specified project."""
    if tool_context is None:
        return {"success": False, "error": "tool context not configured"}
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}],
            },
            "issuetype": {"name": issue_type},
            "priority": {"name": priority},
        }
    }
    url = f"{tool_context.settings.jira_base_url}/rest/api/3/issue"
    result = await request_json("POST", url, headers=_jira_headers(), json_payload=payload)
    if not result["success"]:
        return result
    data = result["data"]
    return {"success": True, "ticket_id": data.get("id"), "ticket_key": data.get("key"), "ticket_url": data.get("self")}


async def update_jira_status(ticket_id: str, status: str) -> dict:
    """Updates the status of an existing Jira ticket."""
    if tool_context is None:
        return {"success": False, "error": "tool context not configured"}
    transitions_url = f"{tool_context.settings.jira_base_url}/rest/api/3/issue/{ticket_id}/transitions"
    transitions = await request_json("GET", transitions_url, headers=_jira_headers())
    if not transitions["success"]:
        return transitions
    target = next((item for item in transitions["data"].get("transitions", []) if item["name"].lower() == status.lower()), None)
    if target is None:
        return {"success": False, "error": f"transition '{status}' not found"}
    result = await request_json(
        "POST",
        transitions_url,
        headers=_jira_headers(),
        json_payload={"transition": {"id": target["id"]}},
    )
    if not result["success"]:
        return result
    return {"success": True, "ticket_id": ticket_id, "status": status}


async def get_jira_ticket(ticket_id: str) -> dict:
    """Retrieves details of a Jira ticket."""
    if tool_context is None:
        return {"success": False, "error": "tool context not configured"}
    url = f"{tool_context.settings.jira_base_url}/rest/api/3/issue/{ticket_id}"
    result = await request_json("GET", url, headers=_jira_headers())
    if not result["success"]:
        return result
    data = result["data"]
    return {"success": True, "ticket_id": data.get("id"), "key": data.get("key"), "status": data.get("fields", {}).get("status", {}).get("name")}


create_jira_ticket_tool = FunctionTool(func=create_jira_ticket)
update_jira_status_tool = FunctionTool(func=update_jira_status)
get_jira_ticket_tool = FunctionTool(func=get_jira_ticket)
