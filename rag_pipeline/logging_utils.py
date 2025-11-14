from __future__ import annotations

import logging
from pathlib import Path

from .config import LoggingConfig, ensure_directories


def configure_logging(config: LoggingConfig) -> None:
    ensure_directories([config.log_file])
    logging.basicConfig(
        level=getattr(logging, config.level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(config.log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

