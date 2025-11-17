"""Project Model"""
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class Project(Base):
    """Project model for organizing RAG documents"""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    chroma_db_path = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships with cascade delete
    conversations = relationship("Conversation", back_populates="project", cascade="all, delete-orphan")
    sources = relationship("Source", cascade="all, delete-orphan", foreign_keys="Source.project_id")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description or "",
            "chroma_db_path": self.chroma_db_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

