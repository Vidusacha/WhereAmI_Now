import asyncio
import json
import requests
import re
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from models import PoliticalEntity

DATABASE_URL = "postgresql+asyncpg://admin:securepassword123@postgres:5432/whereami_db"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

OLLAMA_URL = "http://host.docker.internal:11434/api/chat"

def extract_json(text):
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        return text[start:end+1]
    return text.strip()

def ask_qwen(batch):
    prompt = "Translate or transliterate these Israeli political party names into English and Russian. You MUST wrap your final JSON output in ```json ... ```. The JSON keys MUST be exactly the Hebrew names provided, and values MUST be objects with 'en' and 'ru' keys.\n\n"
    prompt += json.dumps(batch, ensure_ascii=False)
    
    payload = {
        "model": "qwen3.6:latest",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.0, "num_ctx": 4096}
    }
    try:
        res = requests.post(OLLAMA_URL, json=payload, timeout=600)
        if res.status_code == 200:
            msg_content = res.json().get("message", {}).get("content", "")
            json_text = extract_json(msg_content)
            try:
                return json.loads(json_text.strip())
            except Exception:
                return {}
        return {}
    except Exception:
        return {}

async def translate_all():
    async with async_session() as session:
        # Load existing names to avoid unique constraint violations
        existing_result = await session.execute(select(PoliticalEntity.name_en))
        existing_names = {row[0] for row in existing_result.all() if row[0]}
        
        result = await session.execute(select(PoliticalEntity).where(PoliticalEntity.name_en.like('GovIL Party%')))
        entities = result.scalars().all()
        
        batch_size = 5
        total_translated = 0
        
        for i in range(0, len(entities), batch_size):
            batch_entities = entities[i:i+batch_size]
            names = [e.name_he for e in batch_entities]
            print(f"Translating batch {i//batch_size + 1}/{(len(entities)+batch_size-1)//batch_size}... ({len(names)} items)")
            
            translations = ask_qwen(names)
            if not translations:
                continue
                
            for e in batch_entities:
                if e.name_he in translations:
                    tr = translations[e.name_he]
                    if isinstance(tr, dict) and 'en' in tr and 'ru' in tr:
                        en_name = tr['en'].strip()
                        # Deduplicate in memory
                        original_en = en_name
                        counter = 1
                        while en_name in existing_names:
                            en_name = f"{original_en} ({counter})"
                            counter += 1
                        
                        existing_names.add(en_name)
                        e.name_en = en_name
                        e.name_ru = tr['ru'].strip()
                        total_translated += 1
            
            await session.commit()
            print(f"Batch completed. Translated so far: {total_translated}")
            
        print(f"Finished translating {total_translated} out of {len(entities)} parties.")

if __name__ == "__main__":
    asyncio.run(translate_all())
