"""Centralized, structured logging for the UtilityLens backend.

A single ``utilitylen`` logger is configured once and shared across the
service. Log records are emitted as single-line JSON (time, level, logger,
message) so they can be ingested by a log aggregator without leaking any
personal data: callers must never interpolate PII (names, addresses, QR
payloads, API keys) into log messages.
"""

import json
import logging
import sys


class JsonFormatter(logging.Formatter):
    """Formats log records as strict single-line JSON using json.dumps."""

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        formatted_time = self.formatTime(record, self.datefmt or "%Y-%m-%d %H:%M:%S")
        record_dict = {
            "time": formatted_time,
            "level": record.levelname,
            "logger": record.name,
            "msg": record.message,
        }
        if record.exc_info:
            record_dict["exc"] = self.formatException(record.exc_info)
        return json.dumps(record_dict, ensure_ascii=False)


def setup_logging() -> logging.Logger:
    """Configure and return the shared ``utilitylen`` structured logger."""
    logger = logging.getLogger("utilitylen")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


logger = setup_logging()
