"""Conversation and Message Models"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import TYPE_CHECKING
from app.core.database import Base
import uuid

if TYPE_CHECKING:
    from app.models.project import Project


class Conversation(Base):
    """Conversation model"""
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False, default="New Conversation")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    project = relationship("Project", back_populates="conversations")
    
    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Message(Base):
    """Message model"""
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # List of source metadata
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def to_dict(self):
        sources = self.sources or []
        # Extract debug metadata from sources if present
        used_rag = None
        hops = None
        timing = None
        if sources and isinstance(sources, list) and len(sources) > 0:
            first_source = sources[0]
            if isinstance(first_source, dict):
                used_rag = first_source.get("used_rag")
                hops = first_source.get("hops")
                timing = first_source.get("timing")
                # Remove metadata from sources if it's not a real source
                if "used_rag" in first_source and "hops" in first_source and "filename" not in first_source:
                    # This is metadata-only, remove it from sources
                    sources = sources[1:] if len(sources) > 1 else []
        
        result = {
            "role": self.role,
            "content": self.content,
            "sources": sources,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
        
        # Add debug info if available
        if used_rag is not None:
            result["used_rag"] = used_rag
        if hops is not None:
            result["hops"] = hops
        if timing is not None:
            result["timing"] = timing
        
        return result

