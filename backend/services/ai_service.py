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

async def generate_search_queries(entity_name: str, axis_name: str):
    """
    Generates 3 optimal search queries to find the official position of a party on an axis.
    """
    prompt = f"""
    You are an expert researcher. Generate 3 highly specific Google Search queries to find the official position or recent statements of the political entity "{entity_name}" regarding the topic "{axis_name}".
    Output ONLY a JSON array of 3 strings. Example: ["query 1", "query 2", "query 3"]
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
                    queries = json.loads(result.get("response", "[]"))
                    if isinstance(queries, dict):
                        return list(queries.values())
                    return queries
                except:
                    return [f"{entity_name} position on {axis_name}"]
            else:
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
                except:
                    return {"score": 0.0, "confidence": 0.0, "justification_en": "Failed to parse", "justification_ru": "", "justification_he": ""}
            else:
                return {"score": 0.0, "confidence": 0.0, "justification_en": f"API error {response.status}", "justification_ru": "", "justification_he": ""}

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

async def find_duplicate_entities(entities: list[dict]):
    """
    Asks the LLM to identify duplicates in a list of entities (e.g. Likud and Likud - National Liberal Movement).
    entities is a list of dicts: [{'id': 'likud', 'name_en': 'Likud'}, ...]
    Returns a list of dicts: [{'primary_id': 'likud', 'duplicate_id': 'likud_national_liberal_movement'}, ...]
    """
    prompt = f"""
    You are an expert in Israeli politics. Here is a list of political entities in our database:
    {json.dumps(entities, ensure_ascii=False)}
    
    Identify pairs of entities that represent the EXACT SAME political party or faction (e.g., one might be the short name and the other the official registered name).
    Pick the shorter, more common name as the 'primary_id'.
    
    Return ONLY a valid JSON array of objects with keys: 'primary_id' and 'duplicate_id'.
    Example output format:
    [
      {{"primary_id": "likud", "duplicate_id": "likud_national_liberal_movement"}}
    ]
    If no duplicates are found, return [].
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
                    parsed = json.loads(result.get("response", "[]"))
                    
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
                    
                    # Filter out pairs where primary == duplicate just in case
                    valid_pairs = [p for p in extracted_pairs if p["primary_id"] != p["duplicate_id"]]
                    
                    if not valid_pairs:
                        # Fallback: simple heuristic substring matching
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
                                            
                    # Remove reverse duplicates and self-references
                    final_pairs = []
                    seen = set()
                    for p in valid_pairs:
                        if p["primary_id"] == p["duplicate_id"]: continue
                        pair_key = tuple(sorted([p["primary_id"], p["duplicate_id"]]))
                        if pair_key not in seen:
                            seen.add(pair_key)
                            # Ensure primary is the shorter string
                            p1, p2 = p["primary_id"], p["duplicate_id"]
                            if len(p2) < len(p1):
                                p1, p2 = p2, p1
                            final_pairs.append({"primary_id": p1, "duplicate_id": p2})
                            
                    return final_pairs
                except json.JSONDecodeError:
                    return []
            else:
                raise Exception(f"Ollama API error: {response.status}")

async def discover_axes_from_texts(texts: list[str]) -> list[dict]:
    """
    Analyzes documents to discover underlying political axes.
    Returns a list of dicts: [{'name_en': 'axis', 'name_ru': '...', 'name_he': '...', 'description': '...'}]
    """
    combined_text = "\n\n".join(texts)[:8000] # Truncate to avoid context limits
    
    prompt = f"""
    You are an expert political scientist. Read the following political documents and identify 1 to 3 underlying ideological, economic, or social axes (topics/divisions) that these documents touch upon.
    For each axis, provide a short name in English, Russian, and Hebrew, and a brief description in English.
    
    Return ONLY a valid JSON array of objects with these exact keys: 'name_en', 'name_ru', 'name_he', 'description'.
    If you cannot identify any distinct axes, return [].
    
    TEXT:
    {combined_text}
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
                    parsed = json.loads(result.get("response", "[]"))
                    if isinstance(parsed, dict):
                        parsed = [parsed]
                    if isinstance(parsed, list):
                        return [item for item in parsed if isinstance(item, dict)]
                    return []
                except json.JSONDecodeError:
                    return []
            else:
                raise Exception(f"Ollama API error: {response.status}")




