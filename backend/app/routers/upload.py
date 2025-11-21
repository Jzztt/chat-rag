"""File Upload API Router"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from pathlib import Path
from typing import List
import shutil
import hashlib
from app.core.database import get_db
from app.core.config import settings
from app.core.workspace import get_default_workspace
from app.core.semantic_cache import semantic_cache
from app.models.source import Source
from app.services.rag_service import rag_service

router = APIRouter(prefix="/upload", tags=["upload"])


def get_file_hash(file_path: Path) -> str:
    """Calculate MD5 hash of file"""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


@router.post("")
async def upload_files(
    files: List[UploadFile] = File(...),
    conversation_id: str = Query(None, description="Conversation ID to attach sources to"),
    db: Session = Depends(get_db)
):
    """Upload and index files"""
    
    workspace = get_default_workspace()
    
    # Create workspace upload directory (for raw uploads)
    workspace_upload_dir = settings.UPLOAD_DIR / workspace.id
    workspace_upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Create workspace pdfs directory for RAG
    workspace_pdfs_dir = Path(workspace.pdf_dir)
    workspace_pdfs_dir.mkdir(parents=True, exist_ok=True)
    
    uploaded_files = []
    errors = []
    cache_needs_clear = False
    
    for file in files:
        try:
            # Validate file extension
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in settings.ALLOWED_EXTENSIONS:
                errors.append({
                    "filename": file.filename,
                    "error": f"File type {file_ext} not allowed"
                })
                continue
            
            # Validate file size
            file_content = await file.read()
            if len(file_content) > settings.MAX_UPLOAD_SIZE:
                errors.append({
                    "filename": file.filename,
                    "error": f"File size exceeds {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
                })
                continue
            
            # Save file to workspace directory
            file_path = workspace_pdfs_dir / file.filename
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # Index file using RAG service
            try:
                metadata = rag_service.index_file(
                    workspace_id=workspace.id,
                    chroma_db_path=workspace.chroma_db_path,
                    file_path=file_path
                )
                
                # Save source to database (attached to conversation if provided)
                source = Source(
                    conversation_id=conversation_id,  # Attach to conversation (like NotebookLM)
                    filename=metadata["filename"],
                    filepath=metadata["filepath"],
                    file_type=metadata["file_type"],
                    file_size=metadata["file_size"],
                    chunk_count=metadata["chunk_count"],
                    page_count=metadata.get("page_count"),
                    file_hash=get_file_hash(file_path)
                )
                db.add(source)
                db.commit()
                db.refresh(source)
                
                uploaded_files.append({
                    "id": source.id,
                    "filename": source.filename,
                    "status": "completed"
                })
                cache_needs_clear = True
            
            except Exception as e:
                errors.append({
                    "filename": file.filename,
                    "error": f"Error indexing file: {str(e)}"
                })
                # Remove file if indexing failed
                if file_path.exists():
                    file_path.unlink()
        
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": f"Error uploading file: {str(e)}"
            })
    
    # Note: RAG index is already rebuilt in index_file() method
    # No need to rebuild again here
    
    if cache_needs_clear:
        semantic_cache.clear(workspace.id)
    
    return {
        "file_ids": [f["id"] for f in uploaded_files],
        "status": "completed" if not errors else "partial",
        "uploaded": uploaded_files,
        "errors": errors
    }

