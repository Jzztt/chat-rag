"""Sources API Router - Similar to gemini-file-search.py"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.models.source import Source
from app.core.workspace import get_default_workspace
from app.core.semantic_cache import semantic_cache
from app.services.rag_service import rag_service

router = APIRouter(prefix="/sources", tags=["sources"])


class SearchInFileRequest(BaseModel):
    question: str
    filename: str


@router.get("")
async def get_sources(
    conversation_id: str = Query(None, description="Conversation ID to filter sources (optional)"),
    db: Session = Depends(get_db)
):
    """Get sources for the shared knowledge base or specific conversation."""
    workspace = get_default_workspace()
    
    # Get sources from database (filtered by conversation_id if provided)
    query = db.query(Source)
    
    if conversation_id:
        # Only get sources attached to this conversation (like NotebookLM)
        query = query.filter(Source.conversation_id == conversation_id)
    # Otherwise return every source stored in the shared workspace
    
    db_sources = query.all()
    
    # Get RAG index data for metadata
    try:
        rag_sources = rag_service.list_files(workspace.id, workspace.chroma_db_path)
        rag_source_map = {rag["filepath"]: rag for rag in rag_sources}
        
        # Merge database sources with RAG metadata
        sources = []
        for db_source in db_sources:
            source_dict = db_source.to_dict()
            # Add RAG metadata if available
            if db_source.filepath in rag_source_map:
                rag_meta = rag_source_map[db_source.filepath]
                source_dict.update({
                    "file_size_mb": rag_meta.get("file_size_mb"),
                    "file_hash": rag_meta.get("file_hash")
                })
            sources.append(source_dict)
        
        return {"sources": sources}
    except Exception as e:
        # Fallback to database only
        return {"sources": [s.to_dict() for s in db_sources]}


@router.get("/stats")
async def get_sources_stats(
    db: Session = Depends(get_db)
):
    """Get statistics about indexed files (similar to get_file_stats in gemini-file-search.py)"""
    workspace = get_default_workspace()
    
    try:
        stats = rag_service.get_file_stats(workspace.id, workspace.chroma_db_path)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


@router.get("/{source_id}")
async def get_source_details(
    source_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific file (similar to gemini-file-search.py)"""
    workspace = get_default_workspace()
    
    try:
        file_details = rag_service.get_file_details(workspace.id, workspace.chroma_db_path, source_id)
        if not file_details:
            raise HTTPException(status_code=404, detail="Source not found")
        return file_details
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting file details: {str(e)}")


@router.post("/{source_id}/search")
async def search_in_file(
    source_id: str,
    request: SearchInFileRequest,
    db: Session = Depends(get_db)
):
    """Search within a specific file (similar to search_in_file in gemini-file-search.py)"""
    workspace = get_default_workspace()
    
    try:
        result = rag_service.search_in_file(
            workspace_id=workspace.id,
            chroma_db_path=workspace.chroma_db_path,
            question=request.question,
            filename=request.filename
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching in file: {str(e)}")


@router.post("/rebuild")
async def rebuild_index(
    force: bool = Query(False, description="Force rebuild even if index exists"),
    db: Session = Depends(get_db)
):
    """Rebuild the shared RAG index (similar to setup with force_rebuild)."""
    workspace = get_default_workspace()
    
    try:
        result = rag_service.rebuild_index(
            workspace_id=workspace.id,
            chroma_db_path=workspace.chroma_db_path,
            force_rebuild=force
        )
        semantic_cache.clear(workspace.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rebuilding index: {str(e)}")


@router.delete("/{source_id}")
async def delete_source(
    source_id: str,
    conversation_id: str = Query(None, description="Conversation ID (optional, for validation)"),
    db: Session = Depends(get_db)
):
    """Delete a source (like NotebookLM - removes from conversation)"""
    workspace = get_default_workspace()
    
    # Get source
    query = db.query(Source).filter(Source.id == source_id)
    
    # If conversation_id provided, validate it matches
    if conversation_id:
        query = query.filter(Source.conversation_id == conversation_id)
    
    source = query.first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Note: We don't delete from RAG index because:
    # 1. RAG index is shared across all conversations in the workspace
    # 2. Other conversations might still need the file
    # 3. We only remove the source attachment from this conversation (like NotebookLM)
    
    # We also don't delete the physical file because:
    # 1. It might be used by other conversations
    # 2. Files are stored in the workspace pdfs directory (shared)
    # 3. Only the database record (conversation attachment) is removed
    
    # Delete from database (removes source attachment from conversation)
    db.delete(source)
    db.commit()
    semantic_cache.clear(workspace.id)
    
    return {"message": "Source deleted successfully"}

