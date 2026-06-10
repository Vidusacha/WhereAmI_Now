from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
import models
from schemas.schemas import AxisCreate, AxisResponse
from models import ApprovalStatus

router = APIRouter()

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
