from __future__ import annotations

import logging
import logging.handlers
import sys

from .paths import LOG_DIR, ensure_user_dirs


def configure_logging(level: int = logging.INFO) -> None:
    ensure_user_dirs()
    log_path = LOG_DIR / "wgz_updater.log"

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)
