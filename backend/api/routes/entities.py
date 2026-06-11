from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
import models
from schemas.schemas import PoliticalEntityCreate, PoliticalEntityResponse
from models import ApprovalStatus

router = APIRouter()

@router.get("/", response_model=List[PoliticalEntityResponse])
async def get_entities(status: ApprovalStatus = None, db: AsyncSession = Depends(get_db)):
    query = select(models.PoliticalEntity)
    if status:
        query = query.where(models.PoliticalEntity.status == status)
    result = await db.execute(query)
    return result.scalars().all()

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

