from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Sequence

import yaml


@dataclass(frozen=True)
class DataConfig:
    input_dirs: Sequence[Path]
    glob: str = "*.pdf"
    ignore_hidden: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "DataConfig":
        input_dirs = [Path(p) for p in data.get("input_dirs", [])]
        return cls(
            input_dirs=input_dirs,
            glob=data.get("glob", "*.pdf"),
            ignore_hidden=data.get("ignore_hidden", True),
        )


@dataclass(frozen=True)
class ChunkingConfig:
    chunk_size: int = 500
    chunk_overlap: int = 50
    separators: Sequence[str] = field(default_factory=lambda: ("\n\n", "\n", ". ", ".", "!", "?"))

    @classmethod
    def from_dict(cls, data: dict) -> "ChunkingConfig":
        return cls(
            chunk_size=data.get("chunk_size", 500),
            chunk_overlap=data.get("chunk_overlap", 50),
            separators=tuple(data.get("separators", ("\n\n", "\n", ". ", ".", "!", "?"))),
        )


@dataclass(frozen=True)
class EmbeddingConfig:
    model_name: str
    device: str = "cpu"

    @classmethod
    def from_dict(cls, data: dict) -> "EmbeddingConfig":
        return cls(
            model_name=data.get("model_name", "sentence-transformers/all-MiniLM-L6-v2"),
            device=data.get("device", "cpu"),
        )


@dataclass(frozen=True)
class VectorStoreConfig:
    provider: str = "chroma"
    persist_directory: Path = Path("chroma_db")
    collection_name: str = "rag_documents"

    @classmethod
    def from_dict(cls, data: dict) -> "VectorStoreConfig":
        return cls(
            provider=data.get("provider", "chroma"),
            persist_directory=Path(data.get("persist_directory", "chroma_db")),
            collection_name=data.get("collection_name", "rag_documents"),
        )


@dataclass(frozen=True)
class PipelineRuntimeConfig:
    batch_size: int = 100
    manifest_path: Path = Path("artifacts/ingest_manifest.json")

    @classmethod
    def from_dict(cls, data: dict) -> "PipelineRuntimeConfig":
        return cls(
            batch_size=data.get("batch_size", 100),
            manifest_path=Path(data.get("manifest_path", "artifacts/ingest_manifest.json")),
        )


@dataclass(frozen=True)
class LoggingConfig:
    level: str = "INFO"
    log_file: Path = Path("logs/ingest.log")

    @classmethod
    def from_dict(cls, data: dict) -> "LoggingConfig":
        return cls(
            level=data.get("level", "INFO"),
            log_file=Path(data.get("log_file", "logs/ingest.log")),
        )


@dataclass(frozen=True)
class AppConfig:
    data: DataConfig
    chunking: ChunkingConfig
    embedding: EmbeddingConfig
    vector_store: VectorStoreConfig
    pipeline: PipelineRuntimeConfig
    logging: LoggingConfig

    @classmethod
    def load(cls, path: Path) -> "AppConfig":
        with path.open("r", encoding="utf-8") as fh:
            raw_config = yaml.safe_load(fh)
        raw_config = raw_config or {}
        return cls(
            data=DataConfig.from_dict(raw_config.get("data", {})),
            chunking=ChunkingConfig.from_dict(raw_config.get("chunking", {})),
            embedding=EmbeddingConfig.from_dict(raw_config.get("embedding", {})),
            vector_store=VectorStoreConfig.from_dict(raw_config.get("vector_store", {})),
            pipeline=PipelineRuntimeConfig.from_dict(raw_config.get("pipeline", {})),
            logging=LoggingConfig.from_dict(raw_config.get("logging", {})),
        )


def ensure_directories(paths: Iterable[Path]) -> None:
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)

