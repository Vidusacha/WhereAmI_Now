import os
import logging
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

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
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Translate the following text to English. If it is already in English, return the original text. Return ONLY the English translation, no other text:\n\n{text}"
        response = model.generate_content(prompt)
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
