"""Structured local logging. Never logs prompts unless explicitly enabled."""

from __future__ import annotations

import logging
import os
import uuid


_LOGGER_NAME = "lumora"
_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    level_name = os.environ.get("LUMORA_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] lumora %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )
        logger.addHandler(handler)
    logger.propagate = False
    _configured = True


def get_logger() -> logging.Logger:
    _configure()
    return logging.getLogger(_LOGGER_NAME)


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]
