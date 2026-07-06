"""Structured logging setup (structlog).

Call :func:`configure_logging` once at process start (FastAPI does this in
``app.py``). After that, every module just needs::

    import structlog
    log = structlog.get_logger(__name__)
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from multimodal_rag.config import Settings


def configure_logging(settings: Settings) -> None:
    """Configure structlog + stdlib logging in one shot."""
    level = getattr(logging, settings.app_log_level, logging.INFO)

    # Stdlib root logger — captures anything emitted by 3rd-party libs
    logging.basicConfig(
        level=level,
        stream=sys.stdout,
        format="%(message)s",
    )

    # Shared processors for both structlog and stdlib
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            (
                structlog.dev.ConsoleRenderer(colors=True)
                if settings.app_env != "prod"
                else structlog.processors.JSONRenderer()
            ),
        ],
    )

    root = logging.getLogger()
    # Avoid pytest's _LiveLoggingNullHandler (it doesn't support formatters).
    for handler in list(root.handlers):
        if not hasattr(handler, "setFormatter"):
            root.removeHandler(handler)
            continue
        handler.setFormatter(formatter)
    # Ensure there is at least one handler that supports our formatter.
    if not any(hasattr(h, "setFormatter") for h in root.handlers):
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(formatter)
        root.addHandler(h)
