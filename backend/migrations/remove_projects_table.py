"""
Migration: Remove legacy projects table and project_id foreign keys.
Run this script once after pulling the unified workspace changes.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent.parent / "chat_rag.db"


def table_has_column(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    return any(col[1] == column for col in cursor.fetchall())


def recreate_without_column(
    cursor: sqlite3.Cursor,
    table: str,
    create_sql: str,
    columns_to_copy: list[str],
) -> None:
    cursor.execute(f"ALTER TABLE {table} RENAME TO {table}_old")
    cursor.execute(create_sql)
    column_list = ", ".join(columns_to_copy)
    cursor.execute(
        f"INSERT INTO {table} ({column_list}) SELECT {column_list} FROM {table}_old"
    )
    cursor.execute(f"DROP TABLE {table}_old")


def migrate():
    if not DB_PATH.exists():
        print(f"[WARN] Database not found at {DB_PATH}. Nothing to migrate.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # Remove project_id from conversations
        if table_has_column(cursor, "conversations", "project_id"):
            print("➡️  Removing project_id from conversations...")
            recreate_without_column(
                cursor,
                "conversations",
                """
                CREATE TABLE conversations (
                    id TEXT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """,
                ["id", "title", "created_at", "updated_at"],
            )
            print("✅ conversations table updated.")

        # Remove project_id from sources
        if table_has_column(cursor, "sources", "project_id"):
            print("➡️  Removing project_id from sources...")
            recreate_without_column(
                cursor,
                "sources",
                """
                CREATE TABLE sources (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    filename VARCHAR(500) NOT NULL,
                    filepath VARCHAR(1000) NOT NULL,
                    file_type VARCHAR(50) NOT NULL,
                    file_size INTEGER NOT NULL,
                    indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    chunk_count INTEGER DEFAULT 0,
                    page_count INTEGER,
                    file_hash VARCHAR(64)
                )
                """,
                [
                    "id",
                    "conversation_id",
                    "filename",
                    "filepath",
                    "file_type",
                    "file_size",
                    "indexed_at",
                    "chunk_count",
                    "page_count",
                    "file_hash",
                ],
            )
            print("✅ sources table updated.")

        # Drop legacy projects table if it still exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='projects'"
        )
        if cursor.fetchone():
            print("➡️  Dropping legacy projects table...")
            cursor.execute("DROP TABLE projects")
            print("✅ projects table dropped.")

        conn.commit()
        print("[OK] Migration complete.")
    except Exception as exc:
        conn.rollback()
        print(f"[ERROR] Migration failed: {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()

