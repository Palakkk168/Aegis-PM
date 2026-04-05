"""Memory and decision ADK tools."""

from __future__ import annotations

import contextvars
import json

from google.adk.tools import FunctionTool

from memory.decision_log import DecisionLog
from memory.state_store import StateStore
from memory.vector_memory import VectorMemory


current_project_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("current_project_id", default=None)
state_store_singleton = StateStore()
decision_log_singleton = DecisionLog()


def set_project_context(project_id: str) -> None:
    """Set the current project context for tool calls."""
    current_project_id.set(project_id)


async def store_context(text: str, metadata_json: str) -> dict:
    """Stores information in project memory for future retrieval."""
    project_id = current_project_id.get()
    if project_id is None:
        return {"success": False, "error": "project context is not set"}
    metadata = json.loads(metadata_json) if metadata_json else {}
    metadata.setdefault("project_id", project_id)
    memory = VectorMemory.for_project(project_id)
    return await memory.store(text=text, metadata=metadata)


async def retrieve_context(query: str, top_k: int = 5) -> dict:
    """Retrieves relevant past context from project memory."""
    project_id = current_project_id.get()
    if project_id is None:
        return {"success": False, "error": "project context is not set"}
    memory = VectorMemory.for_project(project_id)
    items = await memory.retrieve(query=query, top_k=top_k)
    return {"success": True, "items": items}


async def log_decision(decision_type: str, context: str, outcome: str) -> dict:
    """Logs a decision made during project execution."""
    project_id = current_project_id.get()
    if project_id is None:
        return {"success": False, "error": "project context is not set"}
    return await decision_log_singleton.log(
        project_id=project_id,
        decision_type=decision_type,
        context=context,
        outcome=outcome,
    )


store_context_tool = FunctionTool(func=store_context)
retrieve_context_tool = FunctionTool(func=retrieve_context)
log_decision_tool = FunctionTool(func=log_decision)
