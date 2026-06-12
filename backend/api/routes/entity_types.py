from fastapi import APIRouter, Depends, HTTPException
from typing import List
from database import get_db
import models
from schemas import schemas
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

router = APIRouter()

@router.get("/", response_model=List[schemas.EntityTypeResponse])
async def get_entity_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.EntityType))
    return result.scalars().all()

@router.post("/", response_model=schemas.EntityTypeResponse)
async def create_entity_type(type_in: schemas.EntityTypeCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.EntityType).filter(models.EntityType.id == type_in.id))
    db_type = result.scalars().first()
    if db_type:
        raise HTTPException(status_code=400, detail="Entity Type ID already exists")
    new_type = models.EntityType(**type_in.model_dump())
    db.add(new_type)
    await db.commit()
    await db.refresh(new_type)
    return new_type
