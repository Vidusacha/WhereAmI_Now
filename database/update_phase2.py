import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), 'whereami_core.db')

def update_db():
    logger.info(f"Applying Phase 2 schema updates to {DB_PATH}")
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS party_documents (
                    id TEXT PRIMARY KEY,
                    party_id TEXT,
                    document_text TEXT NOT NULL,
                    source_url TEXT,
                    published_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (party_id) REFERENCES parties_registry(id)
                );
            """)
            conn.commit()
            
        logger.info("Database updated successfully.")
        return True
    except sqlite3.Error as e:
        logger.error(f"An error occurred while updating the database: {e}")
        return False

if __name__ == '__main__':
    update_db()
