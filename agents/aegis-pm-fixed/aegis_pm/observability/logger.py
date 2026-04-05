"""Logging configuration for Aegis PM."""

from __future__ import annotations

import logging

from aegis_pm.config import get_settings


def configure_logging() -> logging.Logger:
    """Configure and return the application logger."""
    settings = get_settings()
    logger = logging.getLogger("aegis_pm")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(settings.log_level.upper())
    logger.propagate = False
    return logger
