from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any
import os

from database import get_db
import models

router = APIRouter()

BASE_DIR = "data/entities"

@router.get("/tree")
async def get_document_tree(db: AsyncSession = Depends(get_db)):
    # Fetch all documents with their entity relation loaded
    query = select(models.ScrapedDocument).options(selectinload(models.ScrapedDocument.entity))
    result = await db.execute(query)
    documents = result.scalars().all()
    
    tree = {"Unassigned": []}
    for doc in documents:
        folder = doc.entity.name_en if doc.entity else "Unassigned"
        if folder not in tree:
            tree[folder] = []
        tree[folder].append({
            "id": doc.id,
            "source_url": doc.source_url,
            "file_path": doc.file_path,
            "scraped_at": doc.scraped_at
        })
    return tree

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    entity_id: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    folder_name = "Unassigned"
    if entity_id:
        # Check if entity exists
        result = await db.execute(select(models.PoliticalEntity).where(models.PoliticalEntity.id == entity_id))
        entity = result.scalars().first()
        if entity:
            folder_name = entity.name_en
        else:
            raise HTTPException(status_code=404, detail="Entity not found")
            
    # Save file
    target_dir = os.path.join(BASE_DIR, folder_name)
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    # Create DB record
    db_doc = models.ScrapedDocument(
        entity_id=entity_id,
        source_url=f"local_upload://{file.filename}",
        file_path=file_path
    )
    db.add(db_doc)
    await db.commit()
    await db.refresh(db_doc)
    
    return {"message": "File uploaded successfully", "document_id": db_doc.id}

@router.get("/files/{path:path}")
async def serve_file(path: str):
    file_path = os.path.join(BASE_DIR, path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)
