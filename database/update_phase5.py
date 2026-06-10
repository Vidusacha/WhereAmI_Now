import sqlite3
import os
import logging
from database.init_db import get_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_db():
    logger.info("Applying Phase 5 schema updates for i18n")
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # dynamic_questionnaires
            try:
                cursor.execute("ALTER TABLE dynamic_questionnaires ADD COLUMN question_text_ru TEXT")
                cursor.execute("ALTER TABLE dynamic_questionnaires ADD COLUMN question_text_he TEXT")
            except sqlite3.OperationalError:
                logger.info("Columns question_text_ru/he might already exist")
                
            # party_simulations
            try:
                cursor.execute("ALTER TABLE party_simulations ADD COLUMN justification_quote_ru TEXT")
                cursor.execute("ALTER TABLE party_simulations ADD COLUMN justification_quote_he TEXT")
            except sqlite3.OperationalError:
                logger.info("Columns justification_quote_ru/he might already exist")
                
            # axes_dictionary
            try:
                cursor.execute("ALTER TABLE axes_dictionary ADD COLUMN pole_minus_1_ru TEXT")
                cursor.execute("ALTER TABLE axes_dictionary ADD COLUMN pole_plus_1_ru TEXT")
                cursor.execute("ALTER TABLE axes_dictionary ADD COLUMN pole_minus_1_he TEXT")
                cursor.execute("ALTER TABLE axes_dictionary ADD COLUMN pole_plus_1_he TEXT")
            except sqlite3.OperationalError:
                logger.info("Columns pole_ru/he might already exist")
                
            conn.commit()
            logger.info("Phase 5 updates applied successfully.")
    except Exception as e:
        logger.error(f"Error during Phase 5 update: {e}")

if __name__ == '__main__':
    update_db()
