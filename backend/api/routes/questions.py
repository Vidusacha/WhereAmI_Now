from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
import models
from schemas.schemas import QuestionCreate, QuestionResponse
from models import ApprovalStatus

router = APIRouter()

@router.get("/", response_model=List[QuestionResponse])
async def get_questions(status: ApprovalStatus = None, db: AsyncSession = Depends(get_db)):
    query = select(models.Question)
    if status:
        query = query.where(models.Question.status == status)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=QuestionResponse)
async def create_question(question: QuestionCreate, db: AsyncSession = Depends(get_db)):
    db_question = models.Question(**question.model_dump())
    db.add(db_question)
    await db.commit()
    await db.refresh(db_question)
    return db_question

@router.put("/{question_id}/approve", response_model=QuestionResponse)
async def approve_question(question_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Question).where(models.Question.id == question_id))
    question = result.scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        
    question.status = ApprovalStatus.APPROVED
    await db.commit()
    await db.refresh(question)
    return question
