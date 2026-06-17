import aiohttp
import json
import os
import re

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.6:latest")

async def call_ollama(prompt: str, force_json: bool = True) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    if force_json:
        payload["format"] = "json"
        
    timeout = aiohttp.ClientTimeout(total=45) # 45 seconds timeout for Ollama
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(f"{OLLAMA_HOST}/api/generate", json=payload) as response:
            if response.status == 200:
                res_data = await response.json()
                return res_data.get("response", "").strip()
            else:
                raise Exception(f"Ollama API HTTP error {response.status}")

async def call_gemini(prompt: str, force_json: bool = True) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    if not api_key:
        raise Exception("Gemini API key not configured")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    if force_json:
        payload["generationConfig"] = {"responseMimeType": "application/json"}
        
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                res_data = await response.json()
                try:
                    return res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                except KeyError:
                    raise Exception(f"Unexpected Gemini response structure: {res_data}")
            else:
                err_text = await response.text()
                raise Exception(f"Gemini API HTTP error {response.status}: {err_text}")

async def generate_ai_response(prompt: str, force_json: bool = True) -> str:
    """
    Tries calling Ollama first. If it fails, returns empty/invalid response, 
    or times out, falls back to Gemini API.
    """
    errors = []
    
    # 1. Try Ollama first
    try:
        print(f"[AI] Attempting Ollama ({OLLAMA_MODEL})...")
        response = await call_ollama(prompt, force_json)
        if response and len(response) > 5:
            if force_json:
                # Validate JSON format
                json.loads(response)
            print("[AI] Ollama successfully answered.")
            return response
        else:
            errors.append(f"Ollama returned empty or too short response: {response!r}")
    except Exception as e:
        errors.append(f"Ollama call failed: {e}")
        
    # 2. Try Gemini API fallback
    if os.getenv("GEMINI_API_KEY"):
        try:
            print("[AI] Ollama failed or returned invalid response. Falling back to Gemini API...")
            response = await call_gemini(prompt, force_json)
            if response:
                print("[AI] Gemini API successfully answered.")
                return response
        except Exception as e:
            errors.append(f"Gemini fallback failed: {e}")
            
    raise Exception(f"AI Generation failed. Errors: {'; '.join(errors)}")

async def analyze_document_for_parties(text_content: str):
    """
    Sends the scraped document to AI to extract political parties.
    """
    prompt = f"""
    You are an expert political analyst. Read the following text and extract all political parties or factions mentioned.
    STRICTLY IGNORE government entities, ministries (e.g., Ministry of Health), or military branches.
    Return ONLY a valid JSON list of dictionaries with keys: 'name_en', 'name_ru', 'name_he'.
    If none are found, return [].
    
    TEXT:
    {text_content[:4000]} # Truncating to avoid context window limits if too long
    """
    try:
        response_text = await generate_ai_response(prompt, force_json=True)
        return json.loads(response_text)
    except Exception as e:
        print(f"Error in analyze_document_for_parties: {e}")
        return []

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
    try:
        response_text = await generate_ai_response(prompt, force_json=True)
        return json.loads(response_text)
    except Exception as e:
        print(f"Error in translate_entity_name: {e}")
        return {"name_en": name, "name_ru": name, "name_he": name}

async def generate_search_queries(entity_name: str, axis_name: str):
    """
    Generates 3 optimal search queries to find the official position of a party on an axis.
    """
    prompt = f"""
    You are an expert researcher. Generate 3 highly specific Google Search queries to find the official position or recent statements of the political entity "{entity_name}" regarding the topic "{axis_name}".
    Output ONLY a JSON array of 3 strings. Example: ["query 1", "query 2", "query 3"]
    """
    try:
        response_text = await generate_ai_response(prompt, force_json=True)
        queries = json.loads(response_text)
        if isinstance(queries, dict):
            return list(queries.values())
        return queries
    except Exception as e:
        print(f"Error in generate_search_queries: {e}")
        return [f"{entity_name} position on {axis_name}"]

async def score_entity_on_axis(entity_name: str, axis_name: str, texts: list[str]):
    """
    Analyzes scraped texts and returns a score, confidence, and multi-lingual justifications.
    """
    combined_text = "\n\n".join(texts)[:8000] # truncate
    prompt = f"""
    You are an expert political analyst. Determine the position of the political entity "{entity_name}" on the issue of "{axis_name}".
    Base your answer strictly on the following text.
    
    Return ONLY a valid JSON object with the following keys:
    'score': float between -1.0 (strongly opposed) and 1.0 (strongly supportive). If unknown, return 0.0.
    'confidence': float between 0.0 and 1.0 indicating how confident you are based on the text.
    'justification_en': A 1-sentence quote or summary in English explaining the score.
    'justification_ru': The same justification translated to Russian.
    'justification_he': The same justification translated to Hebrew.
    
    TEXT:
    {combined_text}
    """
    try:
        response_text = await generate_ai_response(prompt, force_json=True)
        return json.loads(response_text)
    except Exception as e:
        print(f"Error in score_entity_on_axis: {e}")
        return {"score": 0.0, "confidence": 0.0, "justification_en": "Failed to parse", "justification_ru": "", "justification_he": ""}

async def translate_axis_name(name: str):
    """
    Translates a political axis name into English, Russian, and Hebrew.
    """
    prompt = f"""
    You are an expert translator specializing in Israeli politics and sociology.
    Translate the following political axis/topic name into English, Russian, and Hebrew.
    Return ONLY a valid JSON object with exactly these keys: 'name_en', 'name_ru', 'name_he'.
    
    NAME: {name}
    """
    try:
        response_text = await generate_ai_response(prompt, force_json=True)
        return json.loads(response_text)
    except Exception as e:
        print(f"Error in translate_axis_name: {e}")
        return {"name_en": name, "name_ru": name, "name_he": name}

async def find_duplicate_entities(entities: list[dict]):
    """
    Asks the LLM to identify duplicates in a list of entities.
    """
    prompt = f"""
    You are an expert in Israeli politics. Here is a list of political entities in our database:
    {json.dumps(entities, ensure_ascii=False)}
    
    Identify pairs of entities that represent the EXACT SAME political party or faction.
    Pick the shorter, more common name as the 'primary_id'.
    
    Return ONLY a valid JSON array of objects with keys: 'primary_id' and 'duplicate_id'.
    Example output format:
    [
      {{"primary_id": "likud", "duplicate_id": "likud_national_liberal_movement"}}
    ]
    If no duplicates are found, return [].
    """
    try:
        response_text = await generate_ai_response(prompt, force_json=True)
        parsed = json.loads(response_text)
        
        extracted_pairs = []
        def extract_pairs(obj):
            if isinstance(obj, dict):
                if "primary_id" in obj and "duplicate_id" in obj:
                    extracted_pairs.append({
                        "primary_id": str(obj["primary_id"]),
                        "duplicate_id": str(obj["duplicate_id"])
                    })
                for val in obj.values():
                    extract_pairs(val)
            elif isinstance(obj, list):
                for item in obj:
                    extract_pairs(item)
                    
        extract_pairs(parsed)
        valid_pairs = [p for p in extracted_pairs if p["primary_id"] != p["duplicate_id"]]
        
        # Remove reverse duplicates and self-references
        final_pairs = []
        seen = set()
        for p in valid_pairs:
            pair_key = tuple(sorted([p["primary_id"], p["duplicate_id"]]))
            if pair_key not in seen:
                seen.add(pair_key)
                p1, p2 = p["primary_id"], p["duplicate_id"]
                if len(p2) < len(p1):
                    p1, p2 = p2, p1
                final_pairs.append({"primary_id": p1, "duplicate_id": p2})
                
        return final_pairs
    except Exception as e:
        print(f"Error in find_duplicate_entities: {e}")
        # Fallback: simple substring matching
        valid_pairs = []
        for e1 in entities:
            for e2 in entities:
                if e1['id'] != e2['id']:
                    name1 = e1.get('name_en', '').lower()
                    name2 = e2.get('name_en', '').lower()
                    if name1 and name2 and len(name1) > 3 and len(name2) > 3:
                        if name1 in name2:
                            valid_pairs.append({'primary_id': e1['id'], 'duplicate_id': e2['id']})
                        elif name2 in name1:
                            valid_pairs.append({'primary_id': e2['id'], 'duplicate_id': e1['id']})
        return valid_pairs

async def discover_axes_from_texts(texts: list[str]) -> list[dict]:
    """
    Analyzes documents to discover underlying political axes.
    """
    combined_text = "\n\n".join(texts)[:8000]
    prompt = f"""
    You are an expert political scientist. Read the following political documents and identify 1 to 3 underlying ideological, economic, or social axes (topics/divisions) that these documents touch upon.
    For each axis, provide a short name in English, Russian, and Hebrew, and a brief description in English.
    
    Return ONLY a valid JSON array of objects with these exact keys: 'name_en', 'name_ru', 'name_he', 'description'.
    If you cannot identify any distinct axes, return [].
    
    TEXT:
    {combined_text}
    """
    try:
        response_text = await generate_ai_response(prompt, force_json=True)
        parsed = json.loads(response_text)
        if isinstance(parsed, dict):
            parsed = [parsed]
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
        return []
    except Exception as e:
        print(f"Error in discover_axes_from_texts: {e}")
        return []
