import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from contextvars import ContextVar

correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    cid = correlation_id_ctx.get()
    if not cid:
        cid = str(uuid.uuid4())
        correlation_id_ctx.set(cid)
    return cid


def set_correlation_id(cid: str) -> None:
    correlation_id_ctx.set(cid)


class JSONFormatter(logging.Formatter):
    """Outputs structured JSON logs conforming to Google Cloud Logging schema."""

    def __init__(self, service_name: str = "foodbridge"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": record.levelname,
            "message": record.getMessage(),
            "service": self.service_name,
            "correlation_id": correlation_id_ctx.get() or "none",
            "logger": record.name,
            "source_location": {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName,
            },
        }

        # Include extra payload if provided
        if hasattr(record, "payload") and isinstance(record.payload, dict):
            log_entry["payload"] = record.payload

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logger(service_name: str, log_level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers = []

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter(service_name=service_name))
    logger.addHandler(handler)
    logger.propagate = False
    return logger
