from __future__ import annotations

import argparse
from pathlib import Path

from rag_pipeline.config import AppConfig, ensure_directories
from rag_pipeline.logging_utils import configure_logging
from rag_pipeline.pipeline import build_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline indexing pipeline for RAG documents.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/default.yaml"),
        help="Path to the YAML configuration file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = AppConfig.load(args.config)
    configure_logging(config.logging)
    ensure_directories([Path(dir_path) for dir_path in config.data.input_dirs])

    pipeline = build_pipeline(config)
    pipeline.run()


if __name__ == "__main__":
    main()

