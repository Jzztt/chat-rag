"""Source Model"""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Source(Base):
    """Source file model - attached to conversation (like NotebookLM)"""
    __tablename__ = "sources"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)  # Optional: attached to conversation
    filename = Column(String(500), nullable=False)
    filepath = Column(String(1000), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    indexed_at = Column(DateTime(timezone=True), server_default=func.now())
    chunk_count = Column(Integer, default=0)
    page_count = Column(Integer, nullable=True)
    file_hash = Column(String(64), nullable=True)  # MD5 hash for change detection
    
    def to_dict(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "filename": self.filename,
            "filepath": self.filepath,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
            "chunk_count": self.chunk_count,
            "page_count": self.page_count,
        }

