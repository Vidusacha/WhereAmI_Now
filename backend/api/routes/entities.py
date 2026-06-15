from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
import models
from schemas.schemas import PoliticalEntityCreate, PoliticalEntityResponse, EntityScoreResponse
from models import ApprovalStatus

router = APIRouter()

from sqlalchemy.orm import selectinload

@router.get("/", response_model=List[PoliticalEntityResponse])
async def get_entities(status: ApprovalStatus = None, db: AsyncSession = Depends(get_db)):
    query = select(models.PoliticalEntity).options(selectinload(models.PoliticalEntity.documents))
    if status:
        query = query.where(models.PoliticalEntity.status == status)
    result = await db.execute(query)
    entities = result.scalars().all()
    
    for entity in entities:
        entity.doc_count = len(entity.documents)
        entity.last_updated_at = max((d.scraped_at for d in entity.documents if d.scraped_at), default=None)
        
    return entities

@router.post("/", response_model=PoliticalEntityResponse)
async def create_entity(entity: PoliticalEntityCreate, db: AsyncSession = Depends(get_db)):
    # Check if exists
    result = await db.execute(select(models.PoliticalEntity).where(models.PoliticalEntity.id == entity.id))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="PoliticalEntity already exists")
        
    db_entity = models.PoliticalEntity(**entity.model_dump())
    db.add(db_entity)
    await db.commit()
    await db.refresh(db_entity)
    return db_entity

from pydantic import BaseModel
class AutoTranslateRequest(BaseModel):
    name: str
    entity_type_id: str
    
from services import ai_service
import re
import time

@router.post("/auto_translate", response_model=PoliticalEntityResponse)
async def create_entity_auto(req: AutoTranslateRequest, db: AsyncSession = Depends(get_db)):
    translations = await ai_service.translate_entity_name(req.name)
    
    name_en = translations.get("name_en", req.name)
    name_ru = translations.get("name_ru", req.name)
    name_he = translations.get("name_he", req.name)
    
    generated_id = re.sub(r'[^a-z0-9]', '_', name_en.lower().strip())
    if not generated_id:
        generated_id = f"entity_{int(time.time() * 1000)}"
        
    # check exists
    result = await db.execute(select(models.PoliticalEntity).where(models.PoliticalEntity.id == generated_id))
    if result.scalars().first():
        generated_id = f"{generated_id}_{int(time.time() * 1000)}"
        
    db_entity = models.PoliticalEntity(
        id=generated_id,
        name_en=name_en,
        name_ru=name_ru,
        name_he=name_he,
        entity_type_id=req.entity_type_id
    )
    db.add(db_entity)
    await db.commit()
    await db.refresh(db_entity)
    return db_entity

@router.get("/{entity_id}/scores", response_model=List[EntityScoreResponse])
async def get_entity_scores(entity_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.EntityScore).where(models.EntityScore.entity_id == entity_id))
    scores = result.scalars().all()
    return scores

import os
@router.get("/{entity_id}/discovery_log")
async def get_discovery_log(entity_id: str):
    log_path = f"/data/entities/{entity_id}/discovery_log.txt"
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            return {"log": f.read()}
    return {"log": "No discovery log found for this entity. Run 'Discover Discourse' first."}

@router.put("/{entity_id}/approve", response_model=PoliticalEntityResponse)
async def approve_entity(entity_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.PoliticalEntity).where(models.PoliticalEntity.id == entity_id))
    entity = result.scalars().first()
    if not entity:
        raise HTTPException(status_code=404, detail="PoliticalEntity not found")
        
    entity.status = ApprovalStatus.APPROVED
    await db.commit()
    await db.refresh(entity)
    return entity

@router.put("/{entity_id}", response_model=PoliticalEntityResponse)
async def update_entity(entity_id: str, entity_in: PoliticalEntityCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.PoliticalEntity).where(models.PoliticalEntity.id == entity_id))
    entity = result.scalars().first()
    if not entity:
        raise HTTPException(status_code=404, detail="PoliticalEntity not found")
        
    for key, value in entity_in.model_dump().items():
        setattr(entity, key, value)
        
    await db.commit()
    await db.refresh(entity)
    return entity

@router.delete("/{entity_id}")
async def delete_entity(entity_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.PoliticalEntity).where(models.PoliticalEntity.id == entity_id))
    entity = result.scalars().first()
    if not entity:
        raise HTTPException(status_code=404, detail="PoliticalEntity not found")
        
    await db.delete(entity)
    await db.commit()
    return {"status": "ok"}

