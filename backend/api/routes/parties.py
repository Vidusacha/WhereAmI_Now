from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
import models
from schemas.schemas import PartyCreate, PartyResponse
from models import ApprovalStatus

router = APIRouter()

@router.get("/", response_model=List[PartyResponse])
async def get_parties(status: ApprovalStatus = None, db: AsyncSession = Depends(get_db)):
    query = select(models.Party)
    if status:
        query = query.where(models.Party.status == status)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=PartyResponse)
async def create_party(party: PartyCreate, db: AsyncSession = Depends(get_db)):
    # Check if exists
    result = await db.execute(select(models.Party).where(models.Party.id == party.id))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Party already exists")
        
    db_party = models.Party(**party.model_dump())
    db.add(db_party)
    await db.commit()
    await db.refresh(db_party)
    return db_party

@router.put("/{party_id}/approve", response_model=PartyResponse)
async def approve_party(party_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Party).where(models.Party.id == party_id))
    party = result.scalars().first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
        
    party.status = ApprovalStatus.APPROVED
    await db.commit()
    await db.refresh(party)
    return party
