from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import PoliticalEntity, Axis, EntityScore, ApprovalStatus, ScrapedDocument
from schemas.schemas import DiscoveryResponse
from services.search_service import search_duckduckgo
from services.scraper_service import scrape_url
from services.ai_service import generate_search_queries, score_entity_on_axis, discover_axes_from_texts
import traceback
import os

router = APIRouter()

@router.get("/global_log")
async def get_global_discovery_log():
    log_path = "/data/entities/general_news/axis_discovery_log.txt"
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            return {"log": f.read()}
    return {"log": "No unsupervised discovery log found. Run 'Unsupervised Axis Discovery' first."}

@router.post("/discourse/{entity_id}", response_model=DiscoveryResponse)
async def discover_discourse(entity_id: str, db: AsyncSession = Depends(get_db)):
    """
    Reverse Axis Search: Given a political entity, loops over all approved axes,
    searches the web, scrapes the results, and uses AI to score the entity's stance on that axis.
    """
    entity_result = await db.execute(select(PoliticalEntity).where(PoliticalEntity.id == entity_id))
    entity = entity_result.scalar_one_or_none()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
        
    axes_result = await db.execute(select(Axis).where(Axis.status == ApprovalStatus.APPROVED))
    approved_axes = axes_result.scalars().all()
    
    if not approved_axes:
        return DiscoveryResponse(entity_id=entity_id, status="No approved axes found", scores=[], logs=["No approved axes found in database."])
    
    results = []
    logs = []
    
    entity_name_en = entity.name_en
    logs.append(f"Starting discovery for '{entity_name_en}' across {len(approved_axes)} approved axes...")
    
    for axis in approved_axes:
        axis_id = axis.id
        axis_name_en = axis.name_en
        try:
            logs.append(f"\n--- Processing Axis: {axis_name_en} ---")
            # 1. Generate search queries
            queries = await generate_search_queries(entity_name_en, axis_name_en)
            if not queries:
                logs.append("Failed to generate search queries.")
                continue
                
            logs.append(f"Generated queries: {queries}")
            
            # 2. Search DuckDuckGo
            logs.append(f"Searching DuckDuckGo for: '{queries[0]}'")
            urls = await search_duckduckgo(queries[0], max_results=3)
            logs.append(f"Found URLs: {urls}")
            
            scraped_texts = []
            for url in urls:
                # 3. Scrape URL
                try:
                    file_path = await scrape_url(url, entity_id=entity_id)
                    logs.append(f"Successfully scraped: {url}")
                    
                    new_doc = ScrapedDocument(
                        entity_id=entity_id,
                        axis_id=axis_id,
                        source_url=url,
                        file_path=file_path
                    )
                    db.add(new_doc)
                    await db.commit()
                    
                    with open(file_path, "r", encoding="utf-8") as f:
                        scraped_texts.append(f.read())
                except Exception as e:
                    logs.append(f"Failed to scrape {url}: {e}")
                    print(f"Failed to scrape {url}: {e}")
                    await db.rollback()
                    
            if not scraped_texts:
                logs.append("No texts successfully scraped. Skipping AI scoring.")
                continue
                
            # 4. Score Entity
            logs.append("Feeding scraped texts to AI for scoring...")
            ai_result = await score_entity_on_axis(entity_name_en, axis_name_en, scraped_texts)
            logs.append(f"AI Score returned: {ai_result.get('score')} (Confidence: {ai_result.get('confidence')})")
            
            # 5. Upsert to DB
            score_res = await db.execute(select(EntityScore).where(
                EntityScore.entity_id == entity_id,
                EntityScore.axis_id == axis_id
            ))
            existing_score = score_res.scalar_one_or_none()
            
            if existing_score:
                existing_score.score = ai_result.get("score", 0.0)
                existing_score.confidence = ai_result.get("confidence", 0.0)
                existing_score.justification_en = ai_result.get("justification_en", "")
                existing_score.justification_ru = ai_result.get("justification_ru", "")
                existing_score.justification_he = ai_result.get("justification_he", "")
                await db.commit()
                await db.refresh(existing_score)
                results.append(existing_score)
                logs.append("Updated existing score in database.")
            else:
                new_score = EntityScore(
                    entity_id=entity_id,
                    axis_id=axis_id,
                    score=ai_result.get("score", 0.0),
                    confidence=ai_result.get("confidence", 0.0),
                    justification_en=ai_result.get("justification_en", ""),
                    justification_ru=ai_result.get("justification_ru", ""),
                    justification_he=ai_result.get("justification_he", "")
                )
                db.add(new_score)
                await db.commit()
                await db.refresh(new_score)
                results.append(new_score)
                logs.append("Created new score in database.")
                
        except Exception as e:
            logs.append(f"ERROR processing axis '{axis_name_en}': {e}")
            print(f"Error during discovery for axis {axis_id}: {e}")
            traceback.print_exc()
            await db.rollback()

    logs.append("\nDiscovery process completed.")
    
    # Save log to file
    import os
    log_dir = f"/data/entities/{entity_id}"
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, "discovery_log.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(logs))

    return DiscoveryResponse(
        entity_id=entity_id,
        status="Success",
        scores=results,
        logs=logs
    )

@router.post("/axes", response_model=dict)
async def discover_new_axes(db: AsyncSession = Depends(get_db)):
    """Unsupervised Axis Discovery: Scrapes general political news and discovers new axes."""
    logs = []
    logs.append("Starting unsupervised axis discovery from recent news...")
    try:
        urls = await search_duckduckgo("Israeli politics news OR Israel political platforms", max_results=3)
        logs.append(f"Found generic political news URLs: {urls}")
        
        texts = []
        for url in urls:
            try:
                file_path = await scrape_url(url, entity_id="general_news")
                with open(file_path, "r", encoding="utf-8") as f:
                    texts.append(f.read())
                logs.append(f"Successfully scraped: {url}")
            except Exception as e:
                logs.append(f"Failed to scrape {url}: {e}")
                
        if not texts:
            return {"status": "Failed to scrape any news", "logs": logs, "discovered_axes": []}
            
        logs.append("Sending scraped texts to AI for axis discovery...")
        discovered = await discover_axes_from_texts(texts)
        
        saved_axes = []
        for ax_data in discovered:
            name_en = ax_data.get('name_en', 'Unknown Axis')
            existing = await db.execute(select(Axis).where(Axis.name_en == name_en))
            if not existing.scalar_one_or_none():
                import re
                new_id = re.sub(r'[^a-z0-9]', '_', name_en.lower())
                
                # Ensure unique id
                unique_id = new_id
                counter = 1
                while (await db.execute(select(Axis).where(Axis.id == unique_id))).scalar_one_or_none():
                    unique_id = f"{new_id}_{counter}"
                    counter += 1
                    
                new_axis = Axis(
                    id=unique_id,
                    name_en=name_en,
                    name_ru=ax_data.get('name_ru', ''),
                    name_he=ax_data.get('name_he', ''),
                    description=ax_data.get('description', ''),
                    status=ApprovalStatus.PENDING_AI_PROPOSAL
                )
                db.add(new_axis)
                await db.commit()
                await db.refresh(new_axis)
                saved_axes.append(new_axis)
                logs.append(f"Discovered and saved new axis: {new_axis.name_en}")
            else:
                logs.append(f"Axis already exists, skipping: {name_en}")
                
        logs.append(f"Discovery complete. Found {len(saved_axes)} new unique axes.")
        
        log_dir = "/data/entities/general_news"
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "axis_discovery_log.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(logs))
            
        return {"status": "Success", "logs": logs, "discovered_axes": [{"id": ax.id, "name_en": ax.name_en} for ax in saved_axes]}
    except Exception as e:
        logs.append(f"Error during axis discovery: {e}")
        return {"status": "Error", "logs": logs, "discovered_axes": []}

