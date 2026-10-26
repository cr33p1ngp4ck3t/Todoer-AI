import json
import logging
from datetime import datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """Structured JSON logging for observability."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "trace_id"):
            log_entry["trace_id"] = record.trace_id
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
)
