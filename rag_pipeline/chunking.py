from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import ChunkingConfig
from .preprocessing import normalize_text

logger = logging.getLogger(__name__)


@dataclass
class Chunker:
    config: ChunkingConfig

    def split(self, documents: Iterable[Document]) -> List[Document]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=list(self.config.separators),
            length_function=len,
        )
        prepared_documents = [
            Document(page_content=normalize_text(doc.page_content), metadata=doc.metadata) for doc in documents
        ]
        chunks = splitter.split_documents(prepared_documents)
        logger.info("Split documents into %s chunks", len(chunks))
        return chunks

