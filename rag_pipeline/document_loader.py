from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence

from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_core.documents import Document

from .config import DataConfig

logger = logging.getLogger(__name__)


class DocumentLoaderStrategy(ABC):
    """Strategy interface for loading documents from storage."""

    @abstractmethod
    def load(self) -> List[Document]:
        raise NotImplementedError


@dataclass
class PdfDirectoryLoader(DocumentLoaderStrategy):
    config: DataConfig

    def load(self) -> List[Document]:
        documents: List[Document] = []
        for directory in self._iterate_directories():
            logger.info("Loading PDF documents from %s", directory)
            loader = DirectoryLoader(
                path=str(directory),
                glob=self.config.glob,
                loader_cls=PyPDFLoader,
                show_progress=True,
            )
            documents.extend(loader.load())
        logger.info("Loaded %s documents", len(documents))
        return documents

    def _iterate_directories(self) -> Iterator[Path]:
        for raw_dir in self.config.input_dirs:
            if not raw_dir.exists():
                logger.warning("Input directory %s does not exist; skipping", raw_dir)
                continue
            yield raw_dir

