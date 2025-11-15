"""Conversations API Router"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.models.conversation import Conversation

router = APIRouter(prefix="/conversations", tags=["conversations"])


class ConversationCreate(BaseModel):
    project_id: str
    title: Optional[str] = "New Conversation"


class ConversationUpdate(BaseModel):
    title: Optional[str] = None


@router.get("")
async def get_conversations(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    db: Session = Depends(get_db)
):
    """Get all conversations, optionally filtered by project_id"""
    query = db.query(Conversation)
    
    if project_id:
        query = query.filter(Conversation.project_id == project_id)
    
    conversations = query.order_by(Conversation.created_at.desc()).all()
    return {"conversations": [c.to_dict() for c in conversations]}


@router.post("", response_model=dict)
async def create_conversation(
    conversation_data: ConversationCreate,
    db: Session = Depends(get_db)
):
    """Create a new conversation"""
    conversation = Conversation(
        project_id=conversation_data.project_id,
        title=conversation_data.title or "New Conversation"
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return conversation.to_dict()


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Get a conversation by ID"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation.to_dict()


@router.patch("/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    conversation_data: ConversationUpdate,
    db: Session = Depends(get_db)
):
    """Update a conversation (e.g., title)"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation_data.title is not None:
        conversation.title = conversation_data.title
    
    db.commit()
    db.refresh(conversation)
    
    return conversation.to_dict()


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Delete a conversation"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    db.delete(conversation)
    db.commit()
    
    return {"message": "Conversation deleted successfully"}
