import asyncio
import os
import sys

# Ensure backend directory is in path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import async_session_maker
from models import PoliticalEntity
from sqlalchemy import select
from api.services.scraper.orchestrator import run_scraping_job

async def main():
    print("Fetching all political entities from DB...")
    async with async_session_maker() as session:
        result = await session.execute(select(PoliticalEntity))
        entities = result.scalars().all()
        
    print(f"Found {len(entities)} entities.")
    
    total_downloaded = 0
    for entity in entities:
        print(f"\n=========================================")
        print(f"Processing: {entity.name_en} ({entity.name_he})")
        print(f"=========================================")
        try:
            downloaded_files = await run_scraping_job(
                entity_id=entity.id,
                entity_name_en=entity.name_en,
                entity_name_he=entity.name_he
            )
            total_downloaded += len(downloaded_files)
        except Exception as e:
            print(f"Error scraping {entity.name_en}: {e}")
            
    print(f"\nBatch scraping complete! Total documents downloaded: {total_downloaded}")

if __name__ == "__main__":
    asyncio.run(main())
