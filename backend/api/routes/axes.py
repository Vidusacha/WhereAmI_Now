from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
import models
from schemas.schemas import AxisCreate, AxisResponse, AxisUpdate
from models import ApprovalStatus
from services.ai_service import translate_axis_name
import re

router = APIRouter()

@router.put("/{axis_id}", response_model=AxisResponse)
async def update_axis(axis_id: str, axis_update: AxisUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Axis).where(models.Axis.id == axis_id))
    axis = result.scalars().first()
    if not axis:
        raise HTTPException(status_code=404, detail="Axis not found")
    
    if axis_update.name_en is not None:
        axis.name_en = axis_update.name_en
    if axis_update.name_ru is not None:
        axis.name_ru = axis_update.name_ru
    if axis_update.name_he is not None:
        axis.name_he = axis_update.name_he
    if axis_update.description is not None:
        axis.description = axis_update.description
        
    await db.commit()
    await db.refresh(axis)
    return axis

@router.delete("/{axis_id}")
async def delete_axis(axis_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Axis).where(models.Axis.id == axis_id))
    axis = result.scalars().first()
    if not axis:
        raise HTTPException(status_code=404, detail="Axis not found")
    
    await db.delete(axis)
    await db.commit()
    return {"status": "success"}

@router.get("/", response_model=List[AxisResponse])
async def get_axes(status: ApprovalStatus = None, db: AsyncSession = Depends(get_db)):
    query = select(models.Axis)
    if status:
        query = query.where(models.Axis.status == status)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=AxisResponse)
async def create_axis(axis: AxisCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Axis).where(models.Axis.id == axis.id))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Axis already exists")
        
    db_axis = models.Axis(**axis.model_dump())
    db.add(db_axis)
    await db.commit()
    await db.refresh(db_axis)
    return db_axis

@router.put("/{axis_id}/approve", response_model=AxisResponse)
async def approve_axis(axis_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Axis).where(models.Axis.id == axis_id))
    axis = result.scalars().first()
    if not axis:
        raise HTTPException(status_code=404, detail="Axis not found")
        
    axis.status = ApprovalStatus.APPROVED
    await db.commit()
    await db.refresh(axis)
    return axis

@router.post("/auto_translate", response_model=AxisResponse)
async def auto_translate_axis(name: str, db: AsyncSession = Depends(get_db)):
    # Clean the name to create an ID
    axis_id = re.sub(r'[^a-z0-9_]', '', name.lower().replace(" ", "_"))
    
    # Check if exists
    result = await db.execute(select(models.Axis).where(models.Axis.id == axis_id))
    if result.scalars().first():
        # Append random digits if exists
        import random
        axis_id = f"{axis_id}_{random.randint(100, 999)}"
        
    translation = await translate_axis_name(name)
    
    db_axis = models.Axis(
        id=axis_id,
        name_en=translation.get("name_en", name),
        name_ru=translation.get("name_ru", name),
        name_he=translation.get("name_he", name),
        status=ApprovalStatus.PENDING_AI_PROPOSAL
    )
    
    db.add(db_axis)
    await db.commit()
    await db.refresh(db_axis)
    return db_axis
