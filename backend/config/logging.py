from __future__ import annotations

import logging
import logging.config
import os
from contextvars import ContextVar

session_id_var: ContextVar[str | None] = ContextVar("session_id", default=None)


class SessionIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        sid = session_id_var.get()
        if sid:
            record.session_id = sid
        else:
            record.session_id = ""
        return True


_LOGGING_CONFIGURED = False


def configure_logging() -> None:
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return
    _LOGGING_CONFIGURED = True

    level = (os.getenv("LOG_LEVEL") or "INFO").upper()
    pretty = os.getenv("PRETTY_LOGS", "").lower() in ("1", "true", "yes")

    try:
        import pythonjsonlogger  # noqa: F401
        json_formatter: dict = {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s %(session_id)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        }
    except ImportError:
        json_formatter = {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s %(session_id)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        }

    formatters: dict = {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s [%(session_id)s]",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
        "json": json_formatter,
    }

    effective_format = "standard" if pretty else "json"

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "session_id": {
                "()": SessionIdFilter,
            },
        },
        "formatters": formatters,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": effective_format,
                "filters": ["session_id"],
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "livekit": {"level": level, "handlers": ["console"], "propagate": False},
            "core": {"level": level, "handlers": ["console"], "propagate": False},
            "config": {"level": level, "handlers": ["console"], "propagate": False},
            "prompts": {"level": level, "handlers": ["console"], "propagate": False},
            "uvicorn": {"level": level, "handlers": ["console"], "propagate": False},
            "": {"level": level, "handlers": ["console"]},
        },
    })
