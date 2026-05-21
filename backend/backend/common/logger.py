import logging
import sys

from ..config import settings


def _setup_logger() -> logging.Logger:
    log_level = settings.log_level.upper()
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level not in valid_levels:
        log_level = "INFO"

    fmt = "%(asctime)s - %(levelname)s - %(message)s"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))

    logger = logging.getLogger("ink")
    logger.setLevel(log_level)
    logger.addHandler(handler)

    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(log_level)
    uvicorn_logger.addHandler(handler)

    return logger


logger = _setup_logger()
