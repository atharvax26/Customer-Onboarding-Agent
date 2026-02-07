"""
Migration script to add user_id to documents table
This fixes the security issue where users could see each other's documents
"""

import asyncio
import sqlite3
from pathlib import Path

async def migrate_database():
    """Add user_id column to documents table and assign existing documents to first user"""
    
    db_path = Path("customer_onboarding.db")
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    print(f"Migrating database: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if user_id column already exists
        cursor.execute("PRAGMA table_info(documents)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'user_id' in columns:
            print("✓ user_id column already exists in documents table")
            conn.close()
            return
        
        print("Adding user_id column to documents table...")
        
        # Get the first user ID (or create a default user if none exists)
        cursor.execute("SELECT id FROM users LIMIT 1")
        user_row = cursor.fetchone()
        
        if not user_row:
            print("No users found. Please create a user first.")
            conn.close()
            return
        
        default_user_id = user_row[0]
        print(f"Using user ID {default_user_id} as default for existing documents")
        
        # Add user_id column (nullable first)
        cursor.execute("ALTER TABLE documents ADD COLUMN user_id INTEGER")
        
        # Update existing documents to belong to the first user
        cursor.execute("UPDATE documents SET user_id = ?", (default_user_id,))
        
        # Note: SQLite doesn't support adding NOT NULL constraint to existing column
        # We'll handle this at the application level
        
        # Drop the unique constraint on content_hash if it exists
        # SQLite doesn't support dropping constraints directly, so we need to recreate the table
        print("Recreating documents table to remove unique constraint on content_hash...")
        
        # Create new table with updated schema
        cursor.execute("""
            CREATE TABLE documents_new (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                filename VARCHAR NOT NULL,
                original_content TEXT NOT NULL,
                processed_summary JSON,
                step_tasks JSON,
                uploaded_at DATETIME,
                file_size INTEGER,
                content_hash VARCHAR,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Copy data from old table
        cursor.execute("""
            INSERT INTO documents_new 
            SELECT id, user_id, filename, original_content, processed_summary, 
                   step_tasks, uploaded_at, file_size, content_hash
            FROM documents
        """)
        
        # Drop old table
        cursor.execute("DROP TABLE documents")
        
        # Rename new table
        cursor.execute("ALTER TABLE documents_new RENAME TO documents")
        
        # Create indexes
        cursor.execute("CREATE INDEX ix_documents_id ON documents(id)")
        cursor.execute("CREATE INDEX ix_documents_content_hash ON documents(content_hash)")
        cursor.execute("CREATE INDEX ix_documents_user_id ON documents(user_id)")
        
        conn.commit()
        print("✓ Migration completed successfully!")
        print("✓ Documents table now has user_id column")
        print("✓ Existing documents assigned to user", default_user_id)
        print("✓ Unique constraint removed from content_hash (users can upload same doc)")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add user_id to documents")
    print("=" * 60)
    asyncio.run(migrate_database())
    print("=" * 60)
