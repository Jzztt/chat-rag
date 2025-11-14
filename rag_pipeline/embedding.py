from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from .config import EmbeddingConfig

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingStrategy:
    config: EmbeddingConfig

    def __post_init__(self) -> None:
        self._embedding_model = HuggingFaceEmbeddings(
            model_name=self.config.model_name,
            model_kwargs={"device": self.config.device},
        )
        logger.info("Initialized embedding model %s on %s", self.config.model_name, self.config.device)

    @property
    def embedding_model(self) -> HuggingFaceEmbeddings:
        return self._embedding_model

    def embed_documents(self, chunks: List[Document]) -> List[Document]:
        # Chroma handles embedding internally, but this method keeps interface flexible for other vector stores.
        return chunks

