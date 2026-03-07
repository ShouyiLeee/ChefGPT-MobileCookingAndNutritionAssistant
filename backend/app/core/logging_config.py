"""Loguru logging configuration for ChefGPT."""
import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_level: str = "INFO", log_file: str = "logs/chefgpt.log") -> None:
    """Configure loguru handlers: console (colored) + rotating file (JSON)."""
    logger.remove()

    # Console handler — human-readable, colored
    logger.add(
        sys.stdout,
        level=log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
            "{message}"
        ),
        colorize=True,
    )

    # Ensure log directory exists
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # File handler — JSON, rotates at 10MB, keeps 7 days
    logger.add(
        log_file,
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        serialize=True,  # JSON format
        enqueue=True,    # async-safe
    )

    # Separate error log
    error_log = str(Path(log_file).parent / "errors.log")
    logger.add(
        error_log,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        serialize=True,
        enqueue=True,
    )

    logger.info("Logging configured | level={} | file={}", log_level, log_file)
