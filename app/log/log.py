import logging
import os
import time
from typing import Any, Dict

DEFAULT_LOG_FMT: Dict[str, Any] = {
    "format": "%(asctime)s.%(msecs)03dZ %(name)s %(levelname)s: %(message)s",
    "datefmt": "%Y-%m-%dT%H:%M:%S",
}

DEFAULT_UVICORN_LOG_CFG: Dict[str, Any] = {
    "version": 1,
    "formatters": {
        "default": DEFAULT_LOG_FMT,
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "level": "DEBUG",
        },
    },
    "root": {
        "handlers": ["default"],
        "level": "DEBUG",
    },
    "loggers": {
        "uvicorn": {"level": "DEBUG", "propagate": True},
        "uvicorn.error": {"level": "DEBUG", "propagate": True},
        "uvicorn.access": {"level": "DEBUG", "propagate": True},
        "uvicorn.protocols.http.h11_impl": {"level": "DEBUG", "propagate": True},
        "uvicorn.protocols.websockets.websockets_impl": {"level": "DEBUG", "propagate": True},
    },
    "disable_existing_loggers": False,
}


def get_log_level() -> Any:
    """Get the log level from the environment variable or use the default."""
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    try:
        return getattr(logging, log_level)
    except AttributeError as e:
        raise ValueError(f"Invalid log level: {log_level}") from e


def setup_logging(**kwargs) -> None:
    """Configure logging with level taken from environment."""
    config = DEFAULT_LOG_FMT.copy()
    config["level"] = get_log_level()
    config.update(kwargs)

    # Set UTC time for logging
    logging.Formatter.converter = time.gmtime
    # Apply configuration
    logging.basicConfig(**config)


def get_uvicorn_log_config() -> Dict[str, Any]:
    """Get Uvicorn log configuration depending on ENV settings."""
    config = DEFAULT_UVICORN_LOG_CFG.copy()
    config["root"]["level"] = get_log_level()
    config["handlers"]["default"]["level"] = get_log_level()
    return config
