from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List

from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_core.documents import Document

from .config import DataConfig
from .pdf_processor import PdfProcessor, PdfProcessorConfig

logger = logging.getLogger(__name__)


class DocumentLoaderStrategy(ABC):
    """Strategy interface for loading documents from storage."""

    @abstractmethod
    def load(self) -> List[Document]:
        raise NotImplementedError


@dataclass
class PdfDirectoryLoader(DocumentLoaderStrategy):
    config: DataConfig
    pdf_processing_config: PdfProcessorConfig | None = None

    def load(self) -> List[Document]:
        documents: List[Document] = []

        # Nếu có cấu hình xử lý nâng cao (table/image), dùng PdfProcessor
        if self.pdf_processing_config and (
            self.pdf_processing_config.extract_tables or
            self.pdf_processing_config.extract_images
        ):
            processor = PdfProcessor(self.pdf_processing_config)
            for directory in self._iterate_directories():
                logger.info("Loading PDF documents from %s (with advanced processing)", directory)
                pdf_files = list(Path(directory).glob(self.config.glob))
                for pdf_path in pdf_files:
                    try:
                        docs = processor.process_pdf(pdf_path)
                        documents.extend(docs)
                    except Exception as e:
                        logger.error("Error processing %s: %s", pdf_path, e)
        else:
            # Xử lý đơn giản chỉ text (giữ nguyên logic cũ)
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

