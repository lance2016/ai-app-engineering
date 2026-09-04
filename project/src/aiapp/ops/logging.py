"""Structured JSON logs: one object per line, with request id and trace id so a log line can be joined to its trace."""

import json
import logging
import sys
from typing import Any

from aiapp.ops.telemetry import current_trace_id


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {"ts": round(record.created, 3), "level": record.levelname, "logger": record.name, "event": record.getMessage()}
        fields = getattr(record, "fields", None)
        if isinstance(fields, dict):
            payload.update(fields)
        trace_id = current_trace_id()
        if trace_id:
            payload.setdefault("trace_id", trace_id)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_logging(level: int = logging.INFO, stream=None) -> None:
    root = logging.getLogger("aiapp")
    root.handlers.clear()
    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(level)
    root.propagate = False


def log_event(logger: logging.Logger, event: str, level: int = logging.INFO, **fields: Any) -> None:
    logger.log(level, event, extra={"fields": fields})
