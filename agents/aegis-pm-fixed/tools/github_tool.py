"""GitHub ADK tools."""

from __future__ import annotations

from google.adk.tools import FunctionTool

from tools.base_tool import request_json, tool_context


async def create_github_issue(repo: str, title: str, body: str, labels: list[str]) -> dict:
    """Creates a new GitHub issue in the specified repository."""
    if tool_context is None:
        return {"success": False, "error": "tool context not configured"}
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {tool_context.settings.github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    result = await request_json("POST", url, headers=headers, json_payload={"title": title, "body": body, "labels": labels})
    if not result["success"]:
        return result
    data = result["data"]
    return {"success": True, "issue_id": data.get("id"), "issue_url": data.get("html_url"), "number": data.get("number")}


async def create_github_branch(repo: str, branch_name: str, from_branch: str = "main") -> dict:
    """Creates a new branch in a GitHub repository."""
    if tool_context is None:
        return {"success": False, "error": "tool context not configured"}
    headers = {
        "Authorization": f"Bearer {tool_context.settings.github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    source_ref = await request_json("GET", f"https://api.github.com/repos/{repo}/git/ref/heads/{from_branch}", headers=headers)
    if not source_ref["success"]:
        return source_ref
    sha = source_ref["data"]["object"]["sha"]
    payload = {"ref": f"refs/heads/{branch_name}", "sha": sha}
    result = await request_json("POST", f"https://api.github.com/repos/{repo}/git/refs", headers=headers, json_payload=payload)
    if not result["success"]:
        return result
    return {"success": True, "branch_name": branch_name, "ref": result["data"].get("ref"), "sha": sha}


async def get_pr_status(repo: str, pr_number: int) -> dict:
    """Gets the current status of a pull request."""
    if tool_context is None:
        return {"success": False, "error": "tool context not configured"}
    headers = {
        "Authorization": f"Bearer {tool_context.settings.github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    result = await request_json("GET", f"https://api.github.com/repos/{repo}/pulls/{pr_number}", headers=headers)
    if not result["success"]:
        return result
    data = result["data"]
    return {"success": True, "state": data.get("state"), "mergeable": data.get("mergeable"), "url": data.get("html_url")}


create_github_issue_tool = FunctionTool(func=create_github_issue)
create_github_branch_tool = FunctionTool(func=create_github_branch)
get_pr_status_tool = FunctionTool(func=get_pr_status)
