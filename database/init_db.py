import sqlite3
import os
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), 'whereami_core.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def init_db():
    """Initializes the database using the schema.sql file."""
    logger.info(f"Initializing database at {DB_PATH}")
    
    if not os.path.exists(SCHEMA_PATH):
        logger.error(f"Schema file not found at {SCHEMA_PATH}")
        return False
        
    try:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema_script = f.read()
            
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(schema_script)
            conn.commit()
            
        logger.info("Database initialized successfully.")
        return True
    except sqlite3.Error as e:
        logger.error(f"An error occurred while initializing the database: {e}")
        return False

if __name__ == '__main__':
    init_db()
