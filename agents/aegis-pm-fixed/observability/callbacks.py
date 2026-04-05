"""Google ADK callbacks for tracing."""

from __future__ import annotations

from uuid import uuid4

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools.base_tool import BaseTool

from observability.logger import configure_logging
from observability.metrics import metrics_registry


logger = configure_logging()


async def before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> LlmResponse | None:
    """Log ADK model calls and inject a correlation identifier."""
    correlation_id = callback_context.state.get("correlation_id") or uuid4().hex
    callback_context.state["correlation_id"] = correlation_id
    await metrics_registry.increment("llm_calls_total")
    logger.info(
        "llm.before",
        agent=callback_context.agent_name,
        correlation_id=correlation_id,
        message_count=len(llm_request.contents or []),
    )
    return None


async def after_model_callback(callback_context: CallbackContext, llm_response: LlmResponse) -> LlmResponse | None:
    """Log ADK model responses."""
    logger.info(
        "llm.after",
        agent=callback_context.agent_name,
        correlation_id=callback_context.state.get("correlation_id"),
        has_content=bool(llm_response.content),
        partial=llm_response.partial,
    )
    return None


async def before_tool_callback(tool: BaseTool, args: dict, callback_context: CallbackContext) -> dict | None:
    """Log tool invocations before execution."""
    logger.info(
        "tool.before",
        agent=callback_context.agent_name,
        tool=tool.name,
        correlation_id=callback_context.state.get("correlation_id"),
        args=args,
    )
    return None


async def after_tool_callback(tool: BaseTool, args: dict, callback_context: CallbackContext, result: dict) -> dict | None:
    """Log tool results after execution."""
    logger.info(
        "tool.after",
        agent=callback_context.agent_name,
        tool=tool.name,
        correlation_id=callback_context.state.get("correlation_id"),
        args=args,
        result_summary={key: result.get(key) for key in list(result)[:4]},
    )
    return None
