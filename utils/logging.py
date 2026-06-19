"""
Structured logger factory for all agents and team components.
Usage:
    from utils.logging import get_logger
    _log = get_logger(__name__)
    _log.info("message")
"""
import io
import logging
import sys
from config import cfg


def _get_utf8_stream():
    """Return a UTF-8 text stream for logging — safe on Windows cp1252 consoles."""
    try:
        # TextIOWrapper over the raw buffer always uses the requested encoding
        if hasattr(sys.stdout, "buffer"):
            return io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass
    return sys.stdout


_utf8_stream = _get_utf8_stream()


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(_utf8_stream)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        ))
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(getattr(logging, cfg.LOG_LEVEL.upper(), logging.INFO))
    return logger
