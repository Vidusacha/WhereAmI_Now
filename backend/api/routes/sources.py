from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
import models
from schemas.schemas import StaticSourceCreate, StaticSourceResponse

router = APIRouter()

from services.scraper_service import cascade_scrape
from services.ai_service import analyze_document_for_parties
from database import async_session_maker

async def background_scrape_and_analyze(url: str, source_id: int):
    print(f"Starting background scrape for {url}")
    try:
        # Step 1: Scrape (Cascade)
        content = await cascade_scrape(url)
        print(f"Extracted content length: {len(content)}")

            
        # Step 3: Analyze with LLM
        parties_found = await analyze_document_for_parties(content)
        print(f"Ollama found parties: {parties_found}")
        
        # Step 4: Save to DB
        async with async_session_maker() as session:
            # Mark source as scraped
            source = await session.get(models.StaticSource, source_id)
            if source:
                from datetime import datetime
                source.last_scraped_at = datetime.utcnow()
                
            # Create pending proposals
            for p in parties_found:
                party_id = p.get('name_en', '').lower().replace(' ', '_')
                if not party_id: continue
                
                # Check if exists
                existing = await session.get(models.Party, party_id)
                if not existing:
                    new_party = models.Party(
                        id=party_id,
                        name_en=p.get('name_en', ''),
                        name_ru=p.get('name_ru', ''),
                        name_he=p.get('name_he', ''),
                        status=models.ApprovalStatus.PENDING_AI_PROPOSAL
                    )
                    session.add(new_party)
            
            await session.commit()
            
    except Exception as e:
        print(f"Error in background task for {url}: {e}")

@router.get("/", response_model=List[StaticSourceResponse])
async def get_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.StaticSource))
    return result.scalars().all()

@router.post("/", response_model=StaticSourceResponse)
async def create_source(source: StaticSourceCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.StaticSource).where(models.StaticSource.url == source.url))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Source URL already tracked")
        
    db_source = models.StaticSource(**source.model_dump())
    db.add(db_source)
    await db.commit()
    await db.refresh(db_source)
    
    # Trigger background scraping
    background_tasks.add_task(background_scrape_and_analyze, db_source.url, db_source.id)
    
    return db_source
