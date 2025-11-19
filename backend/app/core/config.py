"""Application Configuration"""
import os
import json
from pathlib import Path
from typing import Optional, Union, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_parse_none_str=True,
        env_ignore_empty=True,
    )
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Chat RAG API"
    VERSION: str = "1.0.0"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS Settings - Store as string to avoid auto-parsing, then convert to list
    CORS_ORIGINS_STR: Optional[str] = Field(
        default=None,
        alias="CORS_ORIGINS",
        description="CORS origins as comma-separated string or JSON array"
    )
    
    @property
    def CORS_ORIGINS(self) -> list[str]:
        """Parse CORS_ORIGINS from string to list"""
        if self.CORS_ORIGINS_STR:
            # Try to parse as JSON first
            try:
                parsed = json.loads(self.CORS_ORIGINS_STR)
                if isinstance(parsed, list):
                    return [str(origin) for origin in parsed]
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
            
            # Parse as comma-separated string
            origins = [origin.strip() for origin in self.CORS_ORIGINS_STR.split(',') if origin.strip()]
            if origins:
                return origins
        
        # Default values
        return [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]
    
    # Database Settings
    DATABASE_URL: str = "sqlite:///./chat_rag.db"
    
    # File Upload Settings
    UPLOAD_DIR: Path = Path("./data/uploads")
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: set[str] = {".pdf", ".docx", ".txt", ".md"}
    
    # Workspace Defaults
    DEFAULT_WORKSPACE_ID: str = "global-workspace"
    DEFAULT_WORKSPACE_NAME: str = "Global Workspace"
    DEFAULT_WORKSPACE_DESCRIPTION: str = "Shared knowledge base for all conversations"
    
    # RAG Settings
    RAG_DATA_DIR: Path = Path("./data/pdfs")
    CHROMA_DB_BASE_PATH: Path = Path("./chroma_db")
    FILE_INDEX_PATH: Path = Path("./file_index.json")
    
    @property
    def GLOBAL_CHROMA_DB_PATH(self) -> Path:
        """Path to the shared ChromaDB instance"""
        return self.CHROMA_DB_BASE_PATH / self.DEFAULT_WORKSPACE_ID
    
    @property
    def GLOBAL_PDFS_DIR(self) -> Path:
        """Path for globally stored PDF assets"""
        return self.CHROMA_DB_BASE_PATH / "pdfs"
    
    # Ollama Settings
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Embedding Settings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    DEVICE: str = "cpu"
    
    # RAG Configuration
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K: int = 3
    TEMPERATURE: float = 0.7
    SIMILARITY_THRESHOLD: float = 0.3
    
    # Performance Optimization Settings
    ENABLE_EMBEDDING_CACHE: bool = True
    EMBEDDING_CACHE_SIZE: int = 1000
    MAX_RE_RANK_DOCS: int = 15  # Limit docs for re-ranking
    MAX_SOURCES_TO_PROCESS: int = 5  # Limit sources processed per response
    ENABLE_ASYNC_RETRIEVAL: bool = False  # Future: async retrieval
    REDUCE_MULTI_HOP_BY_DEFAULT: bool = True  # Reduce default max_hops for speed
    DEFAULT_MAX_HOPS: int = 1  # Default to 1 hop instead of 2 for faster responses
    RESPONSE_CACHE_ENABLED: bool = True
    RESPONSE_CACHE_TTL: int = 300  # seconds
    RESPONSE_CACHE_MAX_ENTRIES: int = 200
    
    # Logging
    LOG_DIR: Path = Path("./logs")
    LOG_LEVEL: str = "INFO"


# Create settings instance
settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.RAG_DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_DB_BASE_PATH.mkdir(parents=True, exist_ok=True)
settings.GLOBAL_CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)
settings.GLOBAL_PDFS_DIR.mkdir(parents=True, exist_ok=True)
settings.LOG_DIR.mkdir(parents=True, exist_ok=True)

