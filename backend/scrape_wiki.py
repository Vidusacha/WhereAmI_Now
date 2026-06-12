import asyncio
import requests
import re
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from models import PoliticalEntity

# 1. Scrape Wikipedia
url = "https://he.wikipedia.org/wiki/%D7%9E%D7%A4%D7%9C%D7%92%D7%95%D7%AA_%D7%91%D7%99%D7%A9%D7%A8%D7%90%D7%9C"
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, "html.parser")
tables = soup.find_all("table")

wiki_data = []

def clean_text(text):
    if not text: return ""
    text = re.sub(r"\[.*?\]", "", text)
    # If the text has both hebrew and arabic letters together, just extract the first word (usually Hebrew letters)
    words = text.split()
    if words: return words[0].strip()
    return text.strip()

def clean_name(text):
    if not text: return ""
    text = re.sub(r"\[.*?\]", "", text)
    return text.strip()

# Table 1: Current
if len(tables) > 1:
    for row in tables[1].find_all("tr")[1:]:
        cols = row.find_all(["td", "th"], recursive=False)
        if len(cols) >= 5:
            name = clean_name(cols[1].text)
            letters = clean_text(cols[2].text)
            chairman = clean_name(cols[3].text)
            wiki_data.append({"name": name, "letters": letters, "chairman": chairman})

# Table 12: Registered
if len(tables) > 12:
    for row in tables[12].find_all("tr")[1:]:
        cols = row.find_all(["td", "th"], recursive=False)
        if len(cols) >= 4:
            letters = clean_text(cols[0].text)
            name = clean_name(cols[2].text)
            chairman = clean_name(cols[3].text)
            wiki_data.append({"name": name, "letters": letters, "chairman": chairman})

# Table 21: Historical
if len(tables) > 21:
    for row in tables[21].find_all("tr")[1:]:
        cols = row.find_all(["td", "th"], recursive=False)
        if len(cols) >= 3:
            name = clean_name(cols[0].text)
            letters = clean_text(cols[1].text)
            wiki_data.append({"name": name, "letters": letters, "chairman": ""})

# Normalize names for matching
def normalize(name):
    name = name.replace("~", "").replace("\"", "").replace("'", "").replace("מפלגת ", "").strip()
    if name.startswith("ה") and len(name) > 3: name = name[1:]
    return name

wiki_dict = {}
for item in wiki_data:
    if item["name"]:
        wiki_dict[normalize(item["name"])] = item

# 2. Update DB
DATABASE_URL = "postgresql+asyncpg://admin:securepassword123@postgres:5432/whereami_db"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def update_db():
    async with async_session() as session:
        query = select(PoliticalEntity)
        result = await session.execute(query)
        entities = result.scalars().all()
        
        updated_count = 0
        for entity in entities:
            norm_db_name = normalize(entity.name_he)
            match = None
            
            # 1. exact match
            if norm_db_name in wiki_dict:
                match = wiki_dict[norm_db_name]
            else:
                # 2. Contains match
                for w_name, w_item in wiki_dict.items():
                    if len(w_name) > 3 and len(norm_db_name) > 3:
                        if w_name in norm_db_name or norm_db_name in w_name:
                            match = w_item
                            break
            
            if match:
                changed = False
                if match["letters"] and entity.ballot_letters != match["letters"]:
                    entity.ballot_letters = match["letters"]
                    changed = True
                if match["chairman"] and entity.chairperson != match["chairman"]:
                    entity.chairperson = match["chairman"]
                    changed = True
                if changed:
                    updated_count += 1
        
        await session.commit()
        print(f"Updated {updated_count} parties with letters and chairman from Wikipedia.")

if __name__ == "__main__":
    print(f"Parsed {len(wiki_dict)} unique parties from Wikipedia tables.")
    asyncio.run(update_db())
