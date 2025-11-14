from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from .config import VectorStoreConfig
from .embedding import EmbeddingStrategy

logger = logging.getLogger(__name__)


@dataclass
class VectorStoreManager:
    config: VectorStoreConfig
    embedding_strategy: EmbeddingStrategy

    def persist(self, chunks: List[Document]) -> None:
        if self.config.provider != "chroma":
            raise NotImplementedError(f"Vector store provider {self.config.provider!r} is not supported.")
        logger.info("Persisting %s chunks into Chroma at %s", len(chunks), self.config.persist_directory)
        Chroma.from_documents(
            documents=chunks,
            embedding=self.embedding_strategy.embedding_model,
            persist_directory=str(self.config.persist_directory),
            collection_name=self.config.collection_name,
        )
        logger.info("Vector store persisted successfully.")

