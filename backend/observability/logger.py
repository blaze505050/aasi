"""
AASI Phase 27: Structured Observability Logger.
Outputs machine-readable JSON log records with standard aerospace telemetry fields:
job_id, user_id, experiment_id, provider, geometry_hash, case_hash, manifest_hash,
state, timestamp, error_code.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "job_id": getattr(record, "job_id", None),
            "user_id": getattr(record, "user_id", None),
            "experiment_id": getattr(record, "experiment_id", None),
            "provider": getattr(record, "provider", None),
            "geometry_hash": getattr(record, "geometry_hash", None),
            "case_hash": getattr(record, "case_hash", None),
            "manifest_hash": getattr(record, "manifest_hash", None),
            "state": getattr(record, "state", None),
            "error_code": getattr(record, "error_code", None),
        }
        # Add extra custom fields
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload.update(extra)

        return json.dumps({k: v for k, v in payload.items() if v is not None})


class ObservabilityLogger:
    """Wrapper class for structured observability logging."""
    def __init__(self, name: str = "aasi.observability"):
        self.logger = get_structured_logger(name)

    def log(self, level: int, message: str, **kwargs):
        log_telemetry(level, message, **kwargs)

    def info(self, message: str, **kwargs):
        log_telemetry(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        log_telemetry(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        log_telemetry(logging.ERROR, message, **kwargs)


def get_structured_logger(name: str = "aasi.observability") -> logging.Logger:
    """Configures and returns a structured JSON logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


structured_logger = get_structured_logger()


def log_telemetry(
    level: int,
    message: str,
    job_id: Optional[str] = None,
    user_id: Optional[str] = None,
    experiment_id: Optional[str] = None,
    provider: Optional[str] = None,
    geometry_hash: Optional[str] = None,
    case_hash: Optional[str] = None,
    manifest_hash: Optional[str] = None,
    state: Optional[str] = None,
    error_code: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
):
    """Emit a structured telemetry log entry."""
    record = structured_logger.makeRecord(
        name="aasi.telemetry",
        level=level,
        fn="",
        lno=0,
        msg=message,
        args=(),
        exc_info=None,
    )
    setattr(record, "job_id", job_id)
    setattr(record, "user_id", user_id)
    setattr(record, "experiment_id", experiment_id)
    setattr(record, "provider", provider)
    setattr(record, "geometry_hash", geometry_hash)
    setattr(record, "case_hash", case_hash)
    setattr(record, "manifest_hash", manifest_hash)
    setattr(record, "state", state)
    setattr(record, "error_code", error_code)
    setattr(record, "extra_fields", extra)
    structured_logger.handle(record)
