from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from langchain_core.documents import Document

from .config import AppConfig, ensure_directories
from .document_loader import DocumentLoaderStrategy, PdfDirectoryLoader
from .chunking import Chunker
from .embedding import EmbeddingStrategy
from .vector_store import VectorStoreManager

logger = logging.getLogger(__name__)


@dataclass
class PipelineContext:
    config: AppConfig
    loader: DocumentLoaderStrategy
    chunker: Chunker
    embedder: EmbeddingStrategy
    vector_store: VectorStoreManager


class OfflineIndexPipeline:
    def __init__(self, context: PipelineContext) -> None:
        self.context = context
        ensure_directories(
            [
                context.config.pipeline.manifest_path,
                context.config.vector_store.persist_directory,
            ]
        )

    def run(self) -> None:
        logger.info("Starting offline indexing pipeline.")
        documents = self.context.loader.load()
        if not documents:
            logger.warning("No documents found. Pipeline completed with no changes.")
            return

        chunks = self.context.chunker.split(documents)
        if not chunks:
            logger.warning("No chunks generated. Ensure documents contain valid text.")
            return

        prepared_chunks = self.context.embedder.embed_documents(chunks)
        self.context.vector_store.persist(prepared_chunks)
        self._write_manifest(prepared_chunks)
        logger.info("Offline indexing pipeline completed successfully.")

    def _write_manifest(self, chunks: List[Document]) -> None:
        manifest_path = self.context.config.pipeline.manifest_path
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        unique_sources = {chunk.metadata.get("source") for chunk in chunks}
        data: Dict[str, object] = {
            "documents_indexed": len(unique_sources),
            "chunks_indexed": len(chunks),
            "embedding_model": self.context.config.embedding.model_name,
            "vector_store": {
                "provider": self.context.config.vector_store.provider,
                "persist_directory": str(self.context.config.vector_store.persist_directory),
                "collection_name": self.context.config.vector_store.collection_name,
            },
        }
        with manifest_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        logger.info("Manifest written to %s", manifest_path)


def build_pipeline(config: AppConfig) -> OfflineIndexPipeline:
    loader = PdfDirectoryLoader(config.data)
    chunker = Chunker(config.chunking)
    embedder = EmbeddingStrategy(config.embedding)
    vector_store = VectorStoreManager(config.vector_store, embedder)
    context = PipelineContext(
        config=config,
        loader=loader,
        chunker=chunker,
        embedder=embedder,
        vector_store=vector_store,
    )
    return OfflineIndexPipeline(context)

