"""Projects API Router"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import shutil
import time
from app.core.database import get_db
from app.core.config import settings
from app.models.project import Project
from app.models.conversation import Conversation
from app.models.source import Source
from app.services.rag_service import rag_service

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


@router.get("")
async def get_projects(db: Session = Depends(get_db)):
    """Get all projects"""
    projects = db.query(Project).all()
    return {"projects": [p.to_dict() for p in projects]}


@router.post("", response_model=dict)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db)
):
    """Create a new project"""
    # Create unique chroma_db path for this project
    import uuid
    project_id = str(uuid.uuid4())
    chroma_db_path = str(settings.CHROMA_DB_BASE_PATH / project_id)
    
    # Create directory
    Path(chroma_db_path).mkdir(parents=True, exist_ok=True)
    
    project = Project(
        id=project_id,
        name=project_data.name,
        description=project_data.description or "",
        chroma_db_path=chroma_db_path
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return project.to_dict()


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get a project by ID"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project.to_dict()


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Update a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project_data.name is not None:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    
    db.commit()
    db.refresh(project)
    
    return project.to_dict()


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Delete a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Close RAG system instance to release file handles
    try:
        rag_service.close_rag_system(project_id)
        # Give more time for file handles to be released on Windows
        time.sleep(0.5)
    except Exception as e:
        print(f"Warning: Could not close RAG system: {e}")
    
    # Delete chroma_db directory with retry logic for Windows
    chroma_path = Path(project.chroma_db_path)
    if chroma_path.exists():
        max_retries = 5
        for attempt in range(max_retries):
            try:
                # Try to delete the directory
                shutil.rmtree(chroma_path)
                print(f"✅ Successfully deleted chroma_db directory")
                break
            except PermissionError as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 0.5  # Increasing wait time
                    print(f"Retry {attempt + 1}/{max_retries}: File still in use, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    # Try to close again and force GC
                    try:
                        rag_service.close_rag_system(project_id)
                        import gc
                        gc.collect()
                    except:
                        pass
                else:
                    # Last attempt failed, try to delete individual files
                    print(f"Warning: Could not delete directory after {max_retries} attempts")
                    print(f"Attempting to delete files individually...")
                    try:
                        deleted_count = 0
                        failed_count = 0
                        # Delete files individually (skip locked files)
                        for file_path in chroma_path.rglob('*'):
                            if file_path.is_file():
                                try:
                                    file_path.unlink()
                                    deleted_count += 1
                                except (PermissionError, OSError) as file_error:
                                    failed_count += 1
                                    print(f"Warning: Could not delete {file_path.name}: {file_error}")
                        
                        print(f"Deleted {deleted_count} files, {failed_count} files could not be deleted")
                        
                        # Try to remove empty directories
                        try:
                            # Remove directories from bottom up
                            for dir_path in sorted(chroma_path.rglob('*'), key=lambda p: len(p.parts), reverse=True):
                                if dir_path.is_dir():
                                    try:
                                        dir_path.rmdir()
                                    except:
                                        pass
                            # Try to remove main directory
                            try:
                                chroma_path.rmdir()
                            except:
                                pass
                        except Exception as dir_error:
                            print(f"Warning: Could not remove directories: {dir_error}")
                            
                    except Exception as cleanup_error:
                        print(f"Warning: Could not fully delete chroma_db directory: {cleanup_error}")
                        # Continue with database deletion anyway
            except Exception as e:
                print(f"Warning: Error deleting chroma_db directory: {e}")
                # Continue with database deletion anyway
    
    # Delete related data first (conversations, sources) to avoid foreign key constraint errors
    # Note: With cascade delete in models, this should happen automatically,
    # but we'll do it explicitly to ensure proper order
    
    # Delete sources first (they reference conversations)
    sources_count = db.query(Source).filter(Source.project_id == project_id).delete()
    print(f"Deleted {sources_count} sources")
    
    # Delete conversations (messages will be deleted via cascade)
    conversations_count = db.query(Conversation).filter(Conversation.project_id == project_id).delete()
    print(f"Deleted {conversations_count} conversations")
    
    # Now delete the project
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"}

