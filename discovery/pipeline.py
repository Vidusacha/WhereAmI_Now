import os
import sys
import logging
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables (e.g. GEMINI_API_KEY from .env)
load_dotenv()

from discovery.rss_parser import fetch_daily_news
from discovery.translator import translate_batch
from llm.client import get_llm_client, generate_completion
from database.init_db import get_connection

from utils.logger import setup_audit_logger

logger = setup_audit_logger(__name__)

PROMPT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompts', 'discovery_prompt.txt')

def load_prompt():
    with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
        return f.read()

def get_or_create_party(conn, party_name):
    """Gets the party ID, creating a new party entry if it doesn't exist."""
    cursor = conn.cursor()
    # Normalize name for simple matching
    cursor.execute("SELECT id FROM parties_registry WHERE name = ?", (party_name,))
    row = cursor.fetchone()
    if row:
        return row['id']
    
    party_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO parties_registry (id, name, metadata) VALUES (?, ?, ?)", 
                   (party_id, party_name, json.dumps({"source": "auto_discovery"})))
    conn.commit()
    logger.info(f"Created new party in registry: {party_name}")
    return party_id

def run_pipeline():
    logger.info("Starting Daily Discovery Pipeline")
    
    # 1. Fetch news
    logger.info("=== ALGORITHM STEP 1: Fetching Daily News ===")
    news_items = fetch_daily_news()
    if not news_items:
        logger.warning("No news fetched. Exiting.")
        return

    # 2. Prepare text and translate
    logger.info("=== ALGORITHM STEP 2: Translating News to English ===")
    # We will concatenate the titles and summaries for the LLM context
    texts_to_translate = []
    for item in news_items:
        text = f"Title: {item['title']}\nSummary: {item['summary']}"
        texts_to_translate.append(text)
        
    translated_texts = translate_batch(texts_to_translate)
    
    # Combine translated texts into one large daily summary for the LLM
    daily_summary = "\n\n--- NEWS ITEM ---\n\n".join(translated_texts)
    
    # 3. Call LLM
    logger.info("=== ALGORITHM STEP 3: LLM Analysis for New Axes and Party Statements ===")
    system_prompt = load_prompt()
    client = get_llm_client()
    
    logger.info("Sending summary to LLM for analysis...")
    try:
        response_text = generate_completion(client, system_prompt, daily_summary, temperature=0.2)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return

    # 4. Parse LLM response
    logger.info("=== ALGORITHM STEP 4: Parsing LLM Output ===")
    try:
        # Strip potential markdown blocks if the LLM didn't follow instructions perfectly
        clean_json = response_text.replace('```json', '').replace('```', '').strip()
        analysis = json.loads(clean_json)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}\nResponse was:\n{response_text}")
        return

    new_axes = analysis.get("new_axes", [])
    statements = analysis.get("party_statements", [])
    
    logger.info(f"LLM discovered {len(new_axes)} new axes and {len(statements)} party statements.")

    # 5. Database updates
    logger.info("=== ALGORITHM STEP 5: Database Persistence ===")
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Insert new axes
        for axis in new_axes:
            # Check if exists by ID
            cursor.execute("SELECT id FROM axes_dictionary WHERE id = ?", (axis["id"],))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO axes_dictionary (id, pole_minus_1, pole_plus_1, status) VALUES (?, ?, ?, ?)",
                    (axis["id"], axis["pole_minus_1"], axis["pole_plus_1"], "pending_review")
                )
                logger.info(f"Inserted new axis: {axis['id']}")
                
        # Insert party statements
        for stmt in statements:
            party_name = stmt.get("party_name")
            statement_text = stmt.get("statement")
            
            if not party_name or not statement_text:
                continue
                
            party_id = get_or_create_party(conn, party_name)
            doc_id = str(uuid.uuid4())
            
            cursor.execute(
                "INSERT INTO party_documents (id, party_id, document_text, source_url) VALUES (?, ?, ?, ?)",
                (doc_id, party_id, statement_text, "aggregated_daily_news")
            )
        
        conn.commit()
        logger.info("Database updates completed.")

if __name__ == "__main__":
    run_pipeline()
