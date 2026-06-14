import aiohttp
import json
import os

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen")

async def analyze_document_for_parties(text_content: str):
    """
    Sends the scraped document to Ollama (Qwen) to extract political parties.
    """
    prompt = f"""
    You are an expert political analyst. Read the following text and extract all political parties or factions mentioned.
    STRICTLY IGNORE government entities, ministries (e.g., Ministry of Health), or military branches.
    Return ONLY a valid JSON list of dictionaries with keys: 'name_en', 'name_ru', 'name_he'.
    If none are found, return [].
    
    TEXT:
    {text_content[:4000]} # Truncating to avoid context window limits if too long
    """
    
    async with aiohttp.ClientSession() as session:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json" # Ollama supports JSON mode to force valid JSON output
        }
        
        async with session.post(f"{OLLAMA_HOST}/api/generate", json=payload) as response:
            if response.status == 200:
                result = await response.json()
                try:
                    return json.loads(result.get("response", "[]"))
                except json.JSONDecodeError:
                    print("Failed to decode JSON from Ollama:", result.get("response"))
                    return []
            else:
                raise Exception(f"Ollama API error: {response.status}")

async def translate_entity_name(name: str):
    """
    Translates a political entity name into English, Russian, and Hebrew.
    """
    prompt = f"""
    You are an expert translator specializing in Israeli politics.
    Translate the following political entity name into English, Russian, and Hebrew.
    Return ONLY a valid JSON object with exactly these keys: 'name_en', 'name_ru', 'name_he'.
    
    NAME: {name}
    """
    
    async with aiohttp.ClientSession() as session:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        
        async with session.post(f"{OLLAMA_HOST}/api/generate", json=payload) as response:
            if response.status == 200:
                result = await response.json()
                try:
                    return json.loads(result.get("response", "{}"))
                except json.JSONDecodeError:
                    return {"name_en": name, "name_ru": name, "name_he": name}
            else:
                raise Exception(f"Ollama API error: {response.status}")

