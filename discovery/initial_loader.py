import os
import requests
import json
import time
import sqlite3
import google.generativeai as genai
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from database.init_db import get_connection
from utils.logger import setup_audit_logger

load_dotenv()
logger = setup_audit_logger(__name__)

WIKI_URL = "https://he.wikipedia.org/wiki/%D7%9E%D7%A4%D7%9C%D7%92%D7%95%D7%AA_%D7%91%D7%99%D7%A9%D7%A8%D7%90%D7%9C"

def check_wikipedia_update():
    """Returns True if the Wikipedia page was updated, and the new ETag/Last-Modified."""
    try:
        headers = {'User-Agent': 'WhereAmI_Now/1.0 (Contact: vidusacha@github.com)'}
        response = requests.head(WIKI_URL, headers=headers, timeout=10)
        new_etag = response.headers.get("ETag") or response.headers.get("Last-Modified")
        
        if not new_etag:
            # Fallback if no ETag
            return True, None
            
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_etag FROM sync_metadata WHERE source_url = ?", (WIKI_URL,))
            row = cursor.fetchone()
            
            if row and row['last_etag'] == new_etag:
                return False, new_etag
            
        return True, new_etag
    except Exception as e:
        logger.error(f"Failed to check Wikipedia header: {e}")
        return True, None

def fetch_and_parse_wikipedia():
    """Fetches Wikipedia page, parses main content, and extracts active parties using Gemini."""
    logger.info("Fetching Wikipedia page for initial parties load...")
    try:
        headers = {'User-Agent': 'WhereAmI_Now/1.0 (Contact: vidusacha@github.com)'}
        response = requests.get(WIKI_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        # We only want the main content to avoid huge token counts
        content = soup.find('div', {'id': 'mw-content-text'})
        if not content:
            content = soup # Fallback
            
        text_content = content.get_text(separator=' ', strip=True)[:20000] # Cap to first 20k chars for LLM
        
        logger.info("Sending Wikipedia content to Gemini to extract active parties...")
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY is not set. Cannot parse Wikipedia.")
            return []
            
        genai.configure(api_key=api_key)
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        model = genai.GenerativeModel(model_name)
        
        prompt = """
        You are an expert political scientist. Below is text extracted from the Hebrew Wikipedia page about "Political parties in Israel".
        Your task is to identify ALL currently active political parties in Israel mentioned in the text.
        Return ONLY a raw JSON list of strings containing the English names of these active parties.
        Example: ["Likud", "Yesh Atid", "National Unity"]
        Do not wrap in markdown or backticks. Just the JSON array.
        
        Text:
        """ + text_content
        
        start_time = time.time()
        logger.debug(f"[API CALL START] Gemini extraction from Wikipedia")
        llm_response = model.generate_content(prompt)
        duration = time.time() - start_time
        logger.debug(f"[API CALL END] Gemini extraction took {duration:.2f}s")
        
        # Parse JSON
        raw_text = llm_response.text.strip()
        if raw_text.startswith('```json'):
            raw_text = raw_text.split('```json')[1].split('```')[0].strip()
        elif raw_text.startswith('```'):
            raw_text = raw_text.split('```')[1].split('```')[0].strip()
            
        parties = json.loads(raw_text)
        return parties
    except Exception as e:
        logger.error(f"Error during Wikipedia fetch/parse: {e}")
        return []

def update_registry(parties, new_etag):
    """Inserts new parties into DB and updates sync metadata."""
    if not parties:
        return
        
    inserted_count = 0
    with get_connection() as conn:
        cursor = conn.cursor()
        for party in parties:
            try:
                # generate a simple slug for ID
                party_id = party.lower().replace(" ", "_").replace("'", "").replace('"', "")
                metadata_json = json.dumps({"source": "Wikipedia initial load"})
                cursor.execute(
                    "INSERT INTO parties_registry (id, name, metadata) VALUES (?, ?, ?)",
                    (party_id, party, metadata_json)
                )
                inserted_count += 1
            except sqlite3.IntegrityError:
                pass # Already exists
                
        # Update metadata
        if new_etag:
            cursor.execute("""
                INSERT INTO sync_metadata (source_url, last_etag, last_updated)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(source_url) DO UPDATE SET 
                last_etag=excluded.last_etag,
                last_updated=CURRENT_TIMESTAMP
            """, (WIKI_URL, new_etag))
            
        conn.commit()
    logger.info(f"Initial Load Complete: {inserted_count} new parties added to registry.")

def sync_wikipedia_parties():
    """Main entry point for Step 0 of pipeline."""
    logger.info("=== ALGORITHM STEP 0: Initial Registry Sync ===")
    
    is_updated, new_etag = check_wikipedia_update()
    if not is_updated:
        logger.info("Wikipedia ETag unchanged. Skipping initial load.")
        return
        
    parties = fetch_and_parse_wikipedia()
    if parties:
        logger.info(f"Extracted {len(parties)} parties from Wikipedia.")
        update_registry(parties, new_etag)
