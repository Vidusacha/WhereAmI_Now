import os
import json
import uuid
import time
import google.generativeai as genai
from dotenv import load_dotenv
from database.init_db import get_connection
from utils.logger import setup_audit_logger

load_dotenv()
logger = setup_audit_logger(__name__)

def generate_questions(version="v1.0"):
    logger.info(f"Starting Questionnaire Generation (Version {version})")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, pole_minus_1, pole_plus_1 FROM axes_dictionary")
        axes = cursor.fetchall()
        
        if not axes:
            logger.warning("No axes found in dictionary. Exiting.")
            return

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not set.")
            return
            
        genai.configure(api_key=api_key)
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        model = genai.GenerativeModel(model_name)
        
        generated_count = 0
        for axis in axes:
            # Check if this axis already has a question for this version
            cursor.execute("SELECT id FROM dynamic_questionnaires WHERE axis_id = ? AND questionnaire_version = ?", (axis["id"], version))
            if cursor.fetchone():
                logger.info(f"Question for axis {axis['id']} version {version} already exists. Skipping.")
                continue
                
            prompt = f"""
            You are an expert political sociologist building an interactive questionnaire for voters.
            We have a political axis defined by two poles:
            Pole -1: {axis['pole_minus_1']}
            Pole +1: {axis['pole_plus_1']}
            
            Your task is to generate a SINGLE clear, direct, and neutral question that asks the user where they stand between these two poles.
            The question should be phrased directly to the user (e.g., "Do you believe that...?" or "What is your stance on...?").
            
            Return ONLY the question string. No quotes, no markdown, just the question.
            """
            
            try:
                start_time = time.time()
                response = model.generate_content(prompt)
                duration = time.time() - start_time
                
                question_text = response.text.strip().replace('"', '')
                q_id = str(uuid.uuid4())
                
                cursor.execute(
                    "INSERT INTO dynamic_questionnaires (id, questionnaire_version, axis_id, question_text) VALUES (?, ?, ?, ?)",
                    (q_id, version, axis["id"], question_text)
                )
                conn.commit()
                logger.info(f"Generated question for axis '{axis['id']}': {question_text}")
                generated_count += 1
                
            except Exception as e:
                logger.error(f"Failed to generate question for axis {axis['id']}: {e}")
                
        logger.info(f"Questionnaire generation complete. {generated_count} new questions generated.")

if __name__ == "__main__":
    generate_questions()
