"""Base ADK agent utilities."""

from __future__ import annotations

import json
import re
from typing import Any

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.genai import types
from pydantic import BaseModel

from observability.callbacks import after_model_callback, after_tool_callback, before_model_callback, before_tool_callback


JSON_BLOCK_PATTERN = re.compile(r"\{.*\}|\[.*\]", re.DOTALL)


class BaseAegisAgent(Agent):
    """Base ADK agent with shared callbacks and response parsing."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the ADK agent with common observability callbacks."""
        super().__init__(
            before_model_callback=before_model_callback,
            after_model_callback=after_model_callback,
            before_tool_callback=before_tool_callback,
            after_tool_callback=after_tool_callback,
            **kwargs,
        )

    async def run_structured(
        self,
        runner: Runner,
        *,
        user_id: str,
        session_id: str,
        prompt: str,
        schema: type[BaseModel],
    ) -> BaseModel:
        """Run the ADK agent and parse the final JSON payload."""
        chunks: list[str] = []
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=prompt)]),
        ):
            if event.content is None:
                continue
            for part in event.content.parts or []:
                text = getattr(part, "text", None)
                if text:
                    chunks.append(text)
        raw = "\n".join(chunks)
        match = JSON_BLOCK_PATTERN.search(raw)
        if not match:
            raise ValueError(f"{self.name} did not return structured JSON")
        return schema.model_validate(json.loads(match.group(0)))
