"""
Semantic Cache (CAG) - cache RAG responses using question embeddings.
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from threading import Lock
from typing import Any, Optional

import numpy as np

from app.core.config import settings


class SemanticCache:
    """Semantic cache backed by SQLite."""

    def __init__(
        self,
        db_path: Path,
        similarity_threshold: float,
        max_entries: int,
        lookup_limit: int,
    ):
        self.db_path = Path(db_path)
        self.similarity_threshold = similarity_threshold
        self.max_entries = max_entries
        self.lookup_limit = lookup_limit
        self._lock = Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        workspace_id TEXT NOT NULL,
                        question TEXT NOT NULL,
                        embedding TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        created_at REAL NOT NULL
                    )
                    """
                )
                conn.commit()
            finally:
                conn.close()

    def lookup(
        self,
        workspace_id: str,
        embedding: list[float],
    ) -> Optional[dict[str, Any]]:
        """Return cached payload if similarity is high enough."""
        if not settings.SEMANTIC_CACHE_ENABLED:
            return None

        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    """
                    SELECT id, embedding, payload
                    FROM cache_entries
                    WHERE workspace_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (workspace_id, self.lookup_limit),
                ).fetchall()
            finally:
                conn.close()

        if not rows:
            return None

        query_vec = np.array(embedding, dtype=np.float32)
        if not np.any(query_vec):
            return None

        for row in rows:
            cached_vec = np.array(json.loads(row["embedding"]), dtype=np.float32)
            denom = np.linalg.norm(query_vec) * np.linalg.norm(cached_vec)
            if denom == 0:
                continue
            similarity = float(np.dot(query_vec, cached_vec) / denom)
            if similarity >= self.similarity_threshold:
                payload = json.loads(row["payload"])
                payload = dict(payload)
                payload["cache_hit"] = True
                payload["cache_source"] = "semantic"
                payload["similarity"] = similarity
                return payload

        return None

    def store(
        self,
        workspace_id: str,
        question: str,
        embedding: list[float],
        payload: dict[str, Any],
    ) -> None:
        """Persist payload with associated question embedding."""
        if not settings.SEMANTIC_CACHE_ENABLED:
            return

        serialized_payload = json.dumps(payload, ensure_ascii=False)
        embedding_json = json.dumps(embedding)

        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    """
                    INSERT INTO cache_entries (workspace_id, question, embedding, payload, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (workspace_id, question, embedding_json, serialized_payload, time.time()),
                )
                self._enforce_limit(conn, workspace_id)
                conn.commit()
            finally:
                conn.close()

    def _enforce_limit(self, conn: sqlite3.Connection, workspace_id: str) -> None:
        """Keep only the newest `max_entries` rows per workspace."""
        conn.execute(
            """
            DELETE FROM cache_entries
            WHERE id IN (
                SELECT id FROM cache_entries
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT -1 OFFSET ?
            )
            """,
            (workspace_id, self.max_entries),
        )

    def clear(self, workspace_id: Optional[str] = None) -> None:
        """Clear cache entries (per workspace or globally)."""
        with self._lock:
            conn = self._connect()
            try:
                if workspace_id:
                    conn.execute(
                        "DELETE FROM cache_entries WHERE workspace_id = ?",
                        (workspace_id,),
                    )
                else:
                    conn.execute("DELETE FROM cache_entries")
                conn.commit()
            finally:
                conn.close()


semantic_cache = SemanticCache(
    db_path=settings.SEMANTIC_CACHE_DB_PATH,
    similarity_threshold=settings.SEMANTIC_CACHE_SIMILARITY,
    max_entries=settings.SEMANTIC_CACHE_MAX_ENTRIES,
    lookup_limit=settings.SEMANTIC_CACHE_LOOKUP_LIMIT,
)

