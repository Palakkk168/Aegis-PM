"""Base agent primitives."""

from __future__ import annotations

import logging

from aegis_pm.observability.logger import configure_logging


class BaseAgent:
    """Common base class for all Aegis PM agents."""

    def __init__(self, name: str) -> None:
        """Initialize the agent with a named logger."""
        self.name = name
        root_logger = configure_logging()
        self.logger = logging.getLogger(f"{root_logger.name}.{name.lower()}")
