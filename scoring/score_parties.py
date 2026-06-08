import os
import json
import uuid
import time
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
from database.init_db import get_connection
from utils.logger import setup_audit_logger

load_dotenv()
logger = setup_audit_logger(__name__)

def score_parties(version="v1.0"):
    logger.info(f"Starting Party Scoring Simulation (Version {version})")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Fetch the questionnaire
        cursor.execute("SELECT id, axis_id, question_text FROM dynamic_questionnaires WHERE questionnaire_version = ?", (version,))
        questions = cursor.fetchall()
        
        if not questions:
            logger.warning(f"No questions found for version {version}. Run generate_questions.py first.")
            return
            
        # Also need the axes details to provide context to LLM
        cursor.execute("SELECT id, pole_minus_1, pole_plus_1 FROM axes_dictionary")
        axes_dict = {row["id"]: row for row in cursor.fetchall()}
        
        # 2. Fetch all parties and their documents
        cursor.execute("SELECT id, name FROM parties_registry")
        parties = cursor.fetchall()
        
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not set.")
            return
            
        genai.configure(api_key=api_key)
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        model = genai.GenerativeModel(model_name)
        
        snapshot_id = datetime.now().strftime("%Y-%m-%d")
        
        # Build the axes context for the prompt
        axes_context = ""
        for q in questions:
            axis = axes_dict.get(q["axis_id"])
            if axis:
                axes_context += f"- Axis ID '{axis['id']}': Question: '{q['question_text']}'. Pole -1.0 means '{axis['pole_minus_1']}', Pole +1.0 means '{axis['pole_plus_1']}'.\n"

        scored_count = 0
        
        for party in parties:
            party_id = party["id"]
            
            # Check if this party was already scored today for this version
            cursor.execute("SELECT 1 FROM party_simulations WHERE snapshot_id = ? AND party_id = ? AND questionnaire_version = ?", (snapshot_id, party_id, version))
            if cursor.fetchone():
                logger.info(f"Party {party['name']} already scored for {snapshot_id} {version}. Skipping.")
                continue
                
            cursor.execute("SELECT document_text FROM party_documents WHERE party_id = ?", (party_id,))
            docs = cursor.fetchall()
            
            # Note: We score even if there are no docs, LLM might use general knowledge for famous parties
            party_context = "\n".join([d["document_text"] for d in docs])
            if not party_context:
                party_context = "No specific recent statements in database. Use your general knowledge of this party's established platform in Israel."
            else:
                # Cap context to prevent massive prompts
                party_context = party_context[:30000]
                
            prompt = f"""
            You are an expert political scientist analyzing the Israeli political party "{party['name']}".
            We have a questionnaire with {len(questions)} questions.
            
            Here are the axes and questions:
            {axes_context}
            
            Here are recent statements or known context about the party "{party['name']}":
            {party_context}
            
            Based on this context, estimate how this party would score on each axis.
            The score must be a float between -1.0 and 1.0. 
            Also provide a short 1-2 sentence justification or quote.
            
            Return ONLY a valid JSON array of objects with the following keys:
            - question_id (must match the Axis ID exactly)
            - score (float between -1.0 and 1.0)
            - justification_quote (string)
            
            Example format:
            [
              {{"question_id": "iran_israel_ceasefire_debate", "score": -0.8, "justification_quote": "They strongly advocate for continued military pressure."}}
            ]
            """
            
            try:
                start_time = time.time()
                response = model.generate_content(prompt)
                duration = time.time() - start_time
                
                raw_text = response.text.strip()
                if raw_text.startswith('```json'):
                    raw_text = raw_text.split('```json')[1].split('```')[0].strip()
                elif raw_text.startswith('```'):
                    raw_text = raw_text.split('```')[1].split('```')[0].strip()
                    
                results = json.loads(raw_text)
                
                # Map axis_id back to question_id
                axis_to_qid = {q["axis_id"]: q["id"] for q in questions}
                
                for res in results:
                    axis_id = res.get("question_id") # Note: we told the prompt to output axis ID here
                    score = res.get("score", 0.0)
                    quote = res.get("justification_quote", "")
                    
                    actual_question_id = axis_to_qid.get(axis_id)
                    if actual_question_id:
                        cursor.execute(
                            "INSERT INTO party_simulations (snapshot_id, party_id, question_id, questionnaire_version, score, justification_quote) VALUES (?, ?, ?, ?, ?, ?)",
                            (snapshot_id, party_id, actual_question_id, version, score, quote)
                        )
                        
                conn.commit()
                logger.info(f"Successfully scored party {party['name']} in {duration:.2f}s")
                scored_count += 1
                
            except Exception as e:
                logger.error(f"Failed to score party {party['name']}: {e}")
                
        logger.info(f"Scoring complete. {scored_count} parties processed.")

if __name__ == "__main__":
    score_parties()
