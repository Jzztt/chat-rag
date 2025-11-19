"""
Migration: Add performance indexes for conversation-bound tables.
Run this script once to ensure SQLite has the necessary indexes.
"""
import sqlite3
from pathlib import Path


def migrate():
    db_path = Path(__file__).parent.parent / "chat_rag.db"

    if not db_path.exists():
        print(f"[WARN] Database not found at {db_path}. Nothing to migrate.")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        print("➡️  Creating index idx_messages_conversation_id...")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_conversation_id "
            "ON messages(conversation_id)"
        )

        print("➡️  Creating index idx_sources_conversation_id...")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_sources_conversation_id "
            "ON sources(conversation_id)"
        )

        conn.commit()
        print("[OK] Index migration complete.")
    except Exception as exc:
        conn.rollback()
        print(f"[ERROR] Failed to create indexes: {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()

