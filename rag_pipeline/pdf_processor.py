from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


@dataclass
class PdfProcessorConfig:
    """Cấu hình xử lý PDF."""
    extract_text: bool = True
    extract_tables: bool = False
    extract_images: bool = False
    ocr_language: str = "vie+eng"  # pytesseract language codes
    table_format: str = "markdown"  # "markdown" hoặc "csv"


class PdfProcessor:
    """Xử lý PDF với khả năng extract text, table, và images."""

    def __init__(self, config: PdfProcessorConfig) -> None:
        self.config = config
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """Kiểm tra dependencies cần thiết."""
        missing = []
        if self.config.extract_tables:
            try:
                import pdfplumber  # noqa: F401
            except ImportError:
                missing.append("pdfplumber")
        if self.config.extract_images:
            try:
                import pdf2image  # noqa: F401
                import pytesseract  # noqa: F401
            except ImportError:
                missing.extend(["pdf2image", "pytesseract"])
        if missing:
            logger.warning(
                "Missing dependencies for PDF processing: %s. "
                "Install with: pip install %s",
                ", ".join(missing),
                " ".join(missing)
            )

    def process_pdf(self, pdf_path: Path) -> List[Document]:
        """Xử lý một file PDF và trả về danh sách Document."""
        documents: List[Document] = []

        # 1. Extract text cơ bản (luôn bật)
        if self.config.extract_text:
            text_docs = self._extract_text(pdf_path)
            documents.extend(text_docs)

        # 2. Extract tables
        if self.config.extract_tables:
            table_docs = self._extract_tables(pdf_path)
            documents.extend(table_docs)

        # 3. Extract images + OCR
        if self.config.extract_images:
            image_docs = self._extract_images(pdf_path)
            documents.extend(image_docs)

        return documents

    def _extract_text(self, pdf_path: Path) -> List[Document]:
        """Extract text từ PDF (dùng PyPDFLoader)."""
        from langchain_community.document_loaders import PyPDFLoader

        loader = PyPDFLoader(str(pdf_path))
        docs = loader.load()
        logger.debug("Extracted %d text pages from %s", len(docs), pdf_path.name)
        return docs

    def _extract_tables(self, pdf_path: Path) -> List[Document]:
        """Extract tables từ PDF và chuyển thành text."""
        try:
            import pdfplumber
        except ImportError:
            logger.warning("pdfplumber not installed, skipping table extraction")
            return []

        table_docs: List[Document] = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    tables = page.extract_tables()
                    if not tables:
                        continue

                    for table_idx, table in enumerate(tables, start=1):
                        if not table:
                            continue

                        # Chuyển table thành markdown hoặc text
                        if self.config.table_format == "markdown":
                            table_text = self._table_to_markdown(table)
                        else:
                            table_text = self._table_to_text(table)

                        doc = Document(
                            page_content=table_text,
                            metadata={
                                "source": str(pdf_path),
                                "page": page_num,
                                "type": "table",
                                "table_index": table_idx,
                            }
                        )
                        table_docs.append(doc)

            logger.debug("Extracted %d tables from %s", len(table_docs), pdf_path.name)
        except Exception as e:
            logger.error("Error extracting tables from %s: %s", pdf_path, e)

        return table_docs

    def _table_to_markdown(self, table: List[List[Optional[str]]]) -> str:
        """Chuyển table thành markdown format."""
        if not table:
            return ""

        # Làm sạch dữ liệu
        cleaned = [[str(cell or "").strip() for cell in row] for row in table]
        if not cleaned or not cleaned[0]:
            return ""

        # Tạo markdown table
        lines = []
        header = cleaned[0]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(["---"] * len(header)) + " |")

        for row in cleaned[1:]:
            # Đảm bảo row có đủ cột
            while len(row) < len(header):
                row.append("")
            lines.append("| " + " | ".join(row[:len(header)]) + " |")

        return "\n".join(lines)

    def _table_to_text(self, table: List[List[Optional[str]]]) -> str:
        """Chuyển table thành text format đơn giản."""
        if not table:
            return ""

        lines = []
        for row in table:
            cleaned_row = [str(cell or "").strip() for cell in row]
            lines.append(" | ".join(cleaned_row))
        return "\n".join(lines)

    def _extract_images(self, pdf_path: Path) -> List[Document]:
        """Extract images từ PDF và OCR."""
        try:
            from pdf2image import convert_from_path
            import pytesseract
        except ImportError:
            logger.warning("pdf2image/pytesseract not installed, skipping image extraction")
            return []

        image_docs: List[Document] = []
        try:
            # Convert PDF pages thành images
            images = convert_from_path(pdf_path, dpi=300)
            logger.debug("Converted %d pages to images from %s", len(images), pdf_path.name)

            for page_num, image in enumerate(images, start=1):
                # OCR image
                try:
                    ocr_text = pytesseract.image_to_string(
                        image,
                        lang=self.config.ocr_language
                    ).strip()

                    if ocr_text:
                        doc = Document(
                            page_content=f"[Image OCR from page {page_num}]\n{ocr_text}",
                            metadata={
                                "source": str(pdf_path),
                                "page": page_num,
                                "type": "image_ocr",
                            }
                        )
                        image_docs.append(doc)
                except Exception as e:
                    logger.warning("OCR failed for page %d of %s: %s", page_num, pdf_path, e)

            logger.debug("Extracted %d image OCR documents from %s", len(image_docs), pdf_path.name)
        except Exception as e:
            logger.error("Error extracting images from %s: %s", pdf_path, e)

        return image_docs

