"""
Synaptix Structured Logger.

All services MUST use this logger. Never use print().
Uses structlog for structured, JSON-compatible output.

Usage:
    from packages.shared.logging import get_logger

    logger = get_logger(__name__)
    logger.info("Event name", extra={"key": "value", "tenant_id": str(tenant_id)})
"""

import logging
from typing import Any

import structlog


def configure_logging(log_level: str = "INFO", json_output: bool = False) -> None:
    """Configure the global structlog settings.

    Args:
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR).
        json_output: If True, output JSON instead of console-friendly format.
    """
    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(log_level)),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a named structured logger.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        A structlog BoundLogger instance.
    """
    return structlog.get_logger(name)  # type: ignore[return-value]
