"""Loguru logging configuration for ChefGPT.

Log levels (from most to least verbose):
  TRACE   — ultra-detailed internal steps (disabled in production)
  DEBUG   — cache hit/miss, intent detection, DB query details
  INFO    — normal business events (auth, payments, orders, chat)
  WARNING — recoverable issues (cache down, payment declined, auth failures)
  ERROR   — unexpected failures that need investigation
  CRITICAL — service cannot continue

File outputs:
  logs/chefgpt.log — all DEBUG+ events, JSON, 10 MB rotation, 7-day retention
  logs/errors.log  — ERROR+ events only, JSON, 10 MB rotation, 30-day retention
"""
import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_level: str = "INFO", log_file: str = "logs/chefgpt.log") -> None:
    """Configure loguru handlers: console (colored) + rotating file (JSON)."""
    logger.remove()

    # ── Console handler — human-readable, colored ──────────────────────────────
    logger.add(
        sys.stdout,
        level=log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
            "{message}"
        ),
        colorize=True,
        enqueue=False,  # console is sync, no queue needed
    )

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # ── File handler — JSON, rotates at 10 MB, keeps 7 days ───────────────────
    logger.add(
        log_file,
        level="DEBUG",          # capture DEBUG+ to file (more than console)
        rotation="10 MB",
        retention="7 days",
        serialize=True,         # JSON format for structured log analysis
        enqueue=True,           # async-safe (non-blocking writes)
        compression="gz",       # compress rotated files to save disk
    )

    # ── Separate error log — long retention for post-incident review ───────────
    error_log = str(log_path.parent / "errors.log")
    logger.add(
        error_log,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        serialize=True,
        enqueue=True,
        compression="gz",
    )

    logger.info(
        "logging:configured | console_level={} file={} file_level=DEBUG error_log={}",
        log_level, log_file, error_log,
    )
