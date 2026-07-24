"""
Structured JSON-line logging, suitable for later shipping to any log
aggregator (CloudWatch, ELK, Datadog, etc.) without changing call sites.
"""
import json
import logging
import os
import time

from app.config import LOG_DIR, LOG_FILE

os.makedirs(LOG_DIR, exist_ok=True)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": round(time.time(), 3),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "event"):
            payload["event"] = record.event  # type: ignore[attr-defined]
        if hasattr(record, "data"):
            payload["data"] = record.data  # type: ignore[attr-defined]
        return json.dumps(payload)


def setup_logging() -> None:
    root = logging.getLogger("triage_agent")
    if root.handlers:
        return  # avoid duplicate handlers on reimport (e.g. uvicorn --reload)
    root.setLevel(logging.INFO)

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(JsonFormatter())

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JsonFormatter())

    root.addHandler(file_handler)
    root.addHandler(console_handler)


def log_event(logger: logging.Logger, event: str, **data) -> None:
    """Convenience helper: logger.info with a structured 'event' + 'data' field."""
    logger.info(event, extra={"event": event, "data": data})
