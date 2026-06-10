import os
import sqlite3
import json
import google.generativeai as genai
from dotenv import load_dotenv
import logging
from database.init_db import get_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

def translate_questions():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, question_text FROM dynamic_questionnaires WHERE question_text_ru IS NULL OR question_text_he IS NULL")
        rows = cursor.fetchall()
        
        for row in rows:
            logger.info(f"Translating question: {row['id']}")
            prompt = f"Translate the following political question into Russian and Hebrew. Return ONLY a valid JSON object with keys 'ru' and 'he'.\nQuestion: {row['question_text']}"
            response = model.generate_content(prompt)
            try:
                res_json = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
                cursor.execute("UPDATE dynamic_questionnaires SET question_text_ru = ?, question_text_he = ? WHERE id = ?", (res_json['ru'], res_json['he'], row['id']))
                conn.commit()
            except Exception as e:
                logger.error(f"Error parsing JSON for question {row['id']}: {e}\nRaw response: {response.text}")

def translate_justifications():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT party_id, question_id, justification_quote FROM party_simulations WHERE justification_quote_ru IS NULL OR justification_quote_he IS NULL")
        rows = cursor.fetchall()
        
        for row in rows:
            # logger.info(f"Translating quote for {row['party_id']}")
            prompt = f"Translate the following quote into Russian and Hebrew. Return ONLY a valid JSON object with keys 'ru' and 'he'.\nQuote: {row['justification_quote']}"
            response = model.generate_content(prompt)
            try:
                res_json = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
                cursor.execute("UPDATE party_simulations SET justification_quote_ru = ?, justification_quote_he = ? WHERE party_id = ? AND question_id = ?", 
                               (res_json['ru'], res_json['he'], row['party_id'], row['question_id']))
                conn.commit()
            except Exception as e:
                logger.error(f"Error parsing JSON for quote {row['party_id']}: {e}")

if __name__ == '__main__':
    translate_questions()
    translate_justifications()
    logger.info("Translation complete!")
