"""Utilities for managing the global knowledge base workspace."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from app.core.config import settings


@dataclass(frozen=True)
class WorkspaceInfo:
    """Lightweight representation of the shared workspace."""
    id: str
    name: str
    description: str
    chroma_db_path: str
    pdf_dir: str


def _ensure_workspace_dirs() -> tuple[Path, Path]:
    """Ensure the shared ChromaDB and PDF directories exist."""
    chroma_path = settings.GLOBAL_CHROMA_DB_PATH
    pdf_dir = settings.GLOBAL_PDFS_DIR
    chroma_path.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    return chroma_path, pdf_dir


def get_default_workspace(_: Optional[None] = None) -> WorkspaceInfo:
    """Return metadata about the default (global) workspace."""
    chroma_path, pdf_dir = _ensure_workspace_dirs()
    return WorkspaceInfo(
        id=settings.DEFAULT_WORKSPACE_ID,
        name=settings.DEFAULT_WORKSPACE_NAME,
        description=settings.DEFAULT_WORKSPACE_DESCRIPTION,
        chroma_db_path=str(chroma_path),
        pdf_dir=str(pdf_dir)
    )

