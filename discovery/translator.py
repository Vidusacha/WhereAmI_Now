import os
import logging
import json
import time
import google.generativeai as genai
from dotenv import load_dotenv
from utils.logger import setup_audit_logger

load_dotenv()

logger = setup_audit_logger(__name__)

def setup_gemini():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY environment variable not set.")
    else:
        genai.configure(api_key=api_key)

def translate_to_en(text: str) -> str:
    """
    Translates text (Hebrew/Russian/etc) to English using the Gemini API.
    """
    if not text or not text.strip():
        return ""
        
    try:
        setup_gemini()
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        model = genai.GenerativeModel(model_name)
        prompt = f"Translate the following text to English. If it is already in English, return the original text. Return ONLY the English translation, no other text:\n\n{text}"
        
        start_time = time.time()
        logger.debug(f"[API CALL START] Endpoint: Gemini API (google.generativeai.generate_content) | Model: {model_name} | Prompt:\n{prompt}")
        response = model.generate_content(prompt)
        duration = time.time() - start_time
        logger.debug(f"[API CALL END] Endpoint: Gemini API | Duration: {duration:.2f}s | Response length: {len(response.text)} | Response snippet: {response.text[:100]}...")
        
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini Translation failed: {e}")
        return text # Return original text as fallback

def translate_batch(texts: list) -> list:
    """
    Translates a batch of texts to English.
    """
    logger.info(f"Translating batch of {len(texts)} items using Gemini.")
    return [translate_to_en(t) for t in texts]
