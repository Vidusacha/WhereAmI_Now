import logging
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

def translate_he_to_en(text: str) -> str:
    """
    Translates Hebrew text to English using deep-translator (Google Translate).
    Used as a lightweight proxy for local translation in the dev phase.
    """
    if not text or not text.strip():
        return ""
        
    try:
        translator = GoogleTranslator(source='iw', target='en') # 'iw' is often used for Hebrew in Google Translate
        # Alternatively, 'he' is also supported depending on the library backend
        translator = GoogleTranslator(source='he', target='en')
        
        # Google translator has a 5000 character limit
        if len(text) > 4900:
            text = text[:4900]
            
        translated = translator.translate(text)
        return translated
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return text # Return original text as fallback

def translate_batch(texts: list) -> list:
    """
    Translates a batch of texts.
    """
    logger.info(f"Translating batch of {len(texts)} items.")
    return [translate_he_to_en(t) for t in texts]
