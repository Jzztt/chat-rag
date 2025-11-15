"""
Migration: Add conversation_id to sources table
Run this script to update the database schema
"""
import sqlite3
from pathlib import Path

def migrate():
    """Add conversation_id column to sources table"""
    db_path = Path(__file__).parent.parent / "chat_rag.db"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(sources)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'conversation_id' in columns:
            print("[OK] Column conversation_id already exists")
            return
        
        # Add conversation_id column
        cursor.execute("""
            ALTER TABLE sources 
            ADD COLUMN conversation_id TEXT
        """)
        
        # Add foreign key constraint (SQLite doesn't support ALTER TABLE ADD CONSTRAINT)
        # We'll just add the column, foreign key will be handled by SQLAlchemy
        
        conn.commit()
        print("[OK] Successfully added conversation_id column to sources table")
        
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Error migrating database: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

