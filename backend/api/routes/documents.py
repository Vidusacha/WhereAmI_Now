import os
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from database import get_db
import models
from ..services.scraper.orchestrator import run_scraping_job, DATA_DIR

router = APIRouter()

@router.post("/scrape/{entity_id}")
async def trigger_scraping(entity_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Triggers a background scraping job for a given entity.
    """
    result = await db.execute(select(models.PoliticalEntity).where(models.PoliticalEntity.id == entity_id))
    entity = result.scalar_one_or_none()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
        
    background_tasks.add_task(run_scraping_job, entity.id, entity.name_en, entity.name_he)
    return {"status": "Scraping job started in the background", "entity_id": entity.id}

@router.get("/tree/{entity_id}")
async def get_document_tree(entity_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns a tree structure of scraped and uploaded documents for the entity.
    """
    result = await db.execute(select(models.PoliticalEntity).where(models.PoliticalEntity.id == entity_id))
    entity = result.scalar_one_or_none()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
        
    safe_folder = "".join(c if c.isalnum() or c in " _-" else "_" for c in entity.name_en).strip()
    target_dir = os.path.join(DATA_DIR, safe_folder)
    
    if not os.path.exists(target_dir):
        return {"name": safe_folder, "type": "directory", "children": []}
        
    def build_tree(dir_path):
        tree = []
        for entry in os.scandir(dir_path):
            if entry.is_dir():
                tree.append({
                    "name": entry.name,
                    "type": "directory",
                    "path": os.path.relpath(entry.path, DATA_DIR),
                    "children": build_tree(entry.path)
                })
            else:
                tree.append({
                    "name": entry.name,
                    "type": "file",
                    "path": os.path.relpath(entry.path, DATA_DIR),
                    "size": entry.stat().st_size
                })
        return tree
        
    return {
        "name": safe_folder,
        "type": "directory",
        "path": safe_folder,
        "children": build_tree(target_dir)
    }

@router.post("/upload/{entity_id}")
async def upload_document(entity_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """
    Upload a manual document for the entity.
    """
    result = await db.execute(select(models.PoliticalEntity).where(models.PoliticalEntity.id == entity_id))
    entity = result.scalar_one_or_none()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
        
    safe_folder = "".join(c if c.isalnum() or c in " _-" else "_" for c in entity.name_en).strip()
    target_dir = os.path.join(DATA_DIR, safe_folder)
    os.makedirs(target_dir, exist_ok=True)
    
    file_path = os.path.join(target_dir, file.filename)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    relative_path = os.path.relpath(file_path, DATA_DIR)
    doc = models.ScrapedDocument(
        entity_id=entity_id,
        source_url="Manual Upload",
        file_path=relative_path
    )
    db.add(doc)
    await db.commit()
        
    return {"status": "success", "filename": file.filename}

@router.get("/content")
async def get_document_content(filepath: str):
    """
    Read text/markdown content of a file.
    `filepath` should be relative to DATA_DIR.
    """
    full_path = os.path.abspath(os.path.join(DATA_DIR, filepath))
    
    # Security check to prevent directory traversal
    if not full_path.startswith(os.path.abspath(DATA_DIR)):
        raise HTTPException(status_code=400, detail="Invalid path")
        
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content}
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not readable text")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
