import os
import logging
from openai import OpenAI

import time
from utils.logger import setup_audit_logger

# Configure basic logging
logger = setup_audit_logger(__name__)

# LM Studio default port is 1234
LM_STUDIO_BASE_URL = os.environ.get("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
# API key is not required for LM Studio, but the OpenAI client requires some string
API_KEY = "lm-studio"

def get_llm_client():
    """Returns an OpenAI client configured for the local LM Studio server."""
    logger.info(f"Initializing LLM client pointing to {LM_STUDIO_BASE_URL}")
    client = OpenAI(
        base_url=LM_STUDIO_BASE_URL,
        api_key=API_KEY
    )
    return client

def generate_completion(client: OpenAI, system_prompt: str, user_prompt: str, model: str = "local-model", temperature: float = 0.7):
    """
    Sends a prompt to the local LLM and returns the text response.
    """
    try:
        start_time = time.time()
        logger.debug(f"[API CALL START] Local LLM chat.completions.create with model '{model}'")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
        )
        duration = time.time() - start_time
        logger.debug(f"[API CALL END] Local LLM responded in {duration:.2f}s")
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error communicating with local LLM: {e}")
        raise
