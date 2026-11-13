"""Centralized, structured logging for the UtilityLens backend.

A single ``utilitylen`` logger is configured once and shared across the
service. Log records are emitted as single-line JSON (time, level, logger,
message) so they can be ingested by a log aggregator without leaking any
personal data: callers must never interpolate PII (names, addresses, QR
payloads, API keys) into log messages.
"""

import logging
import sys


def setup_logging() -> logging.Logger:
    """Configure and return the shared ``utilitylen`` structured logger."""
    logger = logging.getLogger("utilitylen")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "msg": "%(message)s"}'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


logger = setup_logging()
