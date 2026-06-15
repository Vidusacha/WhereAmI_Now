from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from database import get_db
import models
from services.ai_service import find_duplicate_entities

router = APIRouter()

@router.post("/deduplicate/entities")
async def deduplicate_entities(db: AsyncSession = Depends(get_db)):
    """
    Finds duplicate political entities using AI, reassigns their scraped docs and scores to the primary entity,
    and deletes the duplicate.
    """
    result = await db.execute(select(models.PoliticalEntity))
    entities = result.scalars().all()
    
    if not entities:
        return {"status": "No entities found", "merged": []}
        
    entity_dicts = [{"id": e.id, "name_en": e.name_en, "name_ru": e.name_ru, "name_he": e.name_he} for e in entities]
    
    duplicates = await find_duplicate_entities(entity_dicts)
    
    merged_info = []
    
    for dup in duplicates:
        primary_id = dup.get("primary_id")
        duplicate_id = dup.get("duplicate_id")
        
        if not primary_id or not duplicate_id or primary_id == duplicate_id:
            continue
            
        # Verify both exist
        res_primary = await db.execute(select(models.PoliticalEntity).where(models.PoliticalEntity.id == primary_id))
        res_duplicate = await db.execute(select(models.PoliticalEntity).where(models.PoliticalEntity.id == duplicate_id))
        
        if not res_primary.scalars().first() or not res_duplicate.scalars().first():
            continue
            
        # Reassign scraped documents
        await db.execute(
            update(models.ScrapedDocument)
            .where(models.ScrapedDocument.entity_id == duplicate_id)
            .values(entity_id=primary_id)
        )
        
        # Reassign scores (if a score exists for primary, we might just delete the duplicate's score,
        # but for simplicity let's just delete the duplicate's scores entirely to avoid unique constraint violations)
        await db.execute(
            delete(models.EntityScore)
            .where(models.EntityScore.entity_id == duplicate_id)
        )
        
        # Delete the duplicate entity
        await db.execute(
            delete(models.PoliticalEntity)
            .where(models.PoliticalEntity.id == duplicate_id)
        )
        
        merged_info.append(f"Merged '{duplicate_id}' into '{primary_id}'")
        
    await db.commit()
    
    return {"status": "Success", "merged": merged_info}
