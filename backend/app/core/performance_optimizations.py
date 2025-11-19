"""
Performance Optimization Utilities
Các hàm tối ưu hóa hiệu suất cho hệ thống RAG
"""
import time
import hashlib
from functools import lru_cache
from typing import Optional, Dict, Any
from threading import Lock

# Global cache for embeddings
_embedding_cache: Dict[str, list] = {}
_embedding_cache_lock = Lock()


def get_cached_embedding(cache_key: str, compute_func, *args, **kwargs) -> list:
    """Cache embeddings để tránh tính toán lại cho cùng một text"""
    with _embedding_cache_lock:
        if cache_key in _embedding_cache:
            return _embedding_cache[cache_key]
    
    embedding = compute_func(*args, **kwargs)
    
    with _embedding_cache_lock:
        # Limit cache size to prevent memory issues
        if len(_embedding_cache) > 1000:
            # Remove oldest 200 entries (simple FIFO)
            keys_to_remove = list(_embedding_cache.keys())[:200]
            for key in keys_to_remove:
                del _embedding_cache[key]
        _embedding_cache[cache_key] = embedding
    
    return embedding


def create_embedding_cache_key(text: str) -> str:
    """Tạo cache key cho embedding"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def clear_embedding_cache():
    """Xóa cache embeddings"""
    with _embedding_cache_lock:
        _embedding_cache.clear()


def batch_embed_documents(embeddings, texts: list, batch_size: int = 32) -> list:
    """Embed documents theo batch để tối ưu"""
    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_results = embeddings.embed_documents(batch)
        results.extend(batch_results)
    return results


def optimize_chroma_search_kwargs(top_k: int = 3) -> Dict[str, Any]:
    """Tối ưu tham số cho ChromaDB search"""
    return {
        "k": min(top_k * 2, 20),  # Search more, filter later
        "score_threshold": 0.0,  # Let re-ranking handle filtering
    }

