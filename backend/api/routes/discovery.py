from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db, async_session_maker
from models import PoliticalEntity, Axis, EntityScore, ApprovalStatus, ScrapedDocument
from schemas.schemas import DiscoveryResponse
from services.search_service import search_google_pse, fetch_latest_news_rss, search_local_documents
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

async def background_discover_discourse_global(session_maker):
    """
    Background job to score all approved entities on all approved axes.
    """
    log_path = "/data/entities/general_news/global_discourse_log.txt"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    def write_log(message: str, mode: str = "a"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, mode, encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
            
    write_log("=== GLOBAL DISCOURSE SCORING JOB STARTED ===", mode="w")
    
    try:
        async with session_maker() as session:
            # 1. Fetch all approved entities
            entities_result = await session.execute(
                select(PoliticalEntity).where(PoliticalEntity.status == ApprovalStatus.APPROVED)
            )
            approved_entities = entities_result.scalars().all()
            
            # 2. Fetch all approved axes
            axes_result = await session.execute(
                select(Axis).where(Axis.status == ApprovalStatus.APPROVED)
            )
            approved_axes = axes_result.scalars().all()
            
            write_log(f"Found {len(approved_entities)} approved entities and {len(approved_axes)} approved axes to score.")
            
            if not approved_entities or not approved_axes:
                write_log("Nothing to score. Completing job.")
                return
                
            total_tasks = len(approved_entities) * len(approved_axes)
            current_task = 0
            
            for entity in approved_entities:
                entity_id = entity.id
                entity_name_en = entity.name_en
                entity_name_ru = entity.name_ru
                entity_name_he = entity.name_he
                
                write_log(f"\n>> Start scoring for entity: {entity_name_en} ({entity_id})")
                
                for axis in approved_axes:
                    axis_id = axis.id
                    axis_name_en = axis.name_en
                    axis_name_ru = axis.name_ru
                    axis_name_he = axis.name_he
                    
                    current_task += 1
                    write_log(f"[{current_task}/{total_tasks}] Scoring {entity_name_en} on Axis {axis_name_en}...")
                    
                    try:
                        # Search local documents
                        local_docs = await search_local_documents(
                            entity_name_en=entity_name_en,
                            entity_name_ru=entity_name_ru,
                            entity_name_he=entity_name_he,
                            axis_name_en=axis_name_en,
                            axis_name_ru=axis_name_ru,
                            axis_name_he=axis_name_he,
                            db=session,
                            limit=5
                        )
                        
                        scraped_texts = []
                        for doc in local_docs:
                            text = doc.content
                            if not text and doc.file_path:
                                resolved_path = doc.file_path
                                if not resolved_path.startswith("/"):
                                    for root_dir in ["/data/scraped_documents", "/data", "/app/data/scraped_documents"]:
                                        cand = os.path.join(root_dir, resolved_path)
                                        if os.path.exists(cand):
                                            resolved_path = cand
                                            break
                                if os.path.exists(resolved_path):
                                    try:
                                        with open(resolved_path, "r", encoding="utf-8") as f:
                                            text = f.read()
                                    except:
                                        pass
                            if text:
                                scraped_texts.append(text)
                                
                        if not scraped_texts:
                            write_log(f"  No local documents found. Attempting Google PSE fallback...")
                            queries = await generate_search_queries(entity_name_en, axis_name_en)
                            if not queries:
                                write_log(f"  Failed to generate queries. Skipping.")
                                continue
                                
                            urls = await search_google_pse(queries[0], max_results=3)
                            write_log(f"  Google PSE found URLs: {urls}")
                            
                            for url in urls:
                                try:
                                    file_path = await scrape_url(url, entity_id=entity_id)
                                    write_log(f"  Successfully scraped: {url}")
                                    
                                    with open(file_path, "r", encoding="utf-8") as f:
                                        file_content = f.read()
                                        
                                    file_content = file_content.replace("\x00", "").replace("\u0000", "")
                                    lines = [l.strip() for l in file_content.split("\n") if l.strip()]
                                    doc_title = lines[0].lstrip("#").strip().strip("*") if lines else "Scraped Article"
                                    doc_title = doc_title.replace("\x00", "").replace("\u0000", "")
                                    
                                    new_doc = ScrapedDocument(
                                        entity_id=entity_id,
                                        axis_id=axis_id,
                                        source_url=url,
                                        file_path=file_path,
                                        title=doc_title[:500],
                                        content=file_content
                                    )
                                    session.add(new_doc)
                                    await session.commit()
                                    scraped_texts.append(file_content)
                                except Exception as e:
                                    write_log(f"  Failed to scrape fallback URL {url}: {e}")
                                    await session.rollback()
                                    
                        if not scraped_texts:
                            write_log(f"  No texts available for scoring. Skipping.")
                            continue
                            
                        write_log(f"  Scoring using AI...")
                        ai_result = await score_entity_on_axis(entity_name_en, axis_name_en, scraped_texts)
                        write_log(f"  AI result: score={ai_result.get('score')}, confidence={ai_result.get('confidence')}")
                        
                        score_res = await session.execute(
                            select(EntityScore).where(
                                EntityScore.entity_id == entity_id,
                                EntityScore.axis_id == axis_id
                            )
                        )
                        existing_score = score_res.scalar_one_or_none()
                        
                        score_val = ai_result.get("score")
                        if score_val is None:
                            score_val = 0.0
                        else:
                            try:
                                score_val = float(score_val)
                            except:
                                score_val = 0.0

                        confidence_val = ai_result.get("confidence")
                        if confidence_val is None:
                            confidence_val = 0.0
                        else:
                            try:
                                confidence_val = float(confidence_val)
                            except:
                                confidence_val = 0.0

                        just_en = ai_result.get("justification_en") or ""
                        just_ru = ai_result.get("justification_ru") or ""
                        just_he = ai_result.get("justification_he") or ""
                        
                        if existing_score:
                            existing_score.score = score_val
                            existing_score.confidence = confidence_val
                            existing_score.justification_en = just_en
                            existing_score.justification_ru = just_ru
                            existing_score.justification_he = just_he
                            write_log(f"  Updated existing score in database.")
                        else:
                            new_score = EntityScore(
                                entity_id=entity_id,
                                axis_id=axis_id,
                                score=score_val,
                                confidence=confidence_val,
                                justification_en=just_en,
                                justification_ru=just_ru,
                                justification_he=just_he
                            )
                            session.add(new_score)
                            write_log(f"  Created new score in database.")
                            
                        await session.commit()
                        
                    except Exception as ex:
                        write_log(f"  ERROR processing axis '{axis_name_en}': {ex}")
                        await session.rollback()
                        
            write_log("=== GLOBAL DISCOURSE SCORING JOB COMPLETED SUCCESSFULLY ===")
    except Exception as e:
        write_log(f"CRITICAL ERROR in background global scoring: {e}")


@router.post("/discourse/all")
async def discover_discourse_all(background_tasks: BackgroundTasks):
    """
    Triggers global scoring for all approved entities on all approved axes.
    """
    background_tasks.add_task(background_discover_discourse_global, async_session_maker)
    return {"status": "Global discourse scoring job started in the background"}


@router.get("/global_discourse_log")
async def get_global_discourse_log():
    log_path = "/data/entities/general_news/global_discourse_log.txt"
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            return {"log": f.read()}
    return {"log": "No global discourse scoring log found. Click 'Discover Discourse (All Entities)' to start."}


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
            
            # 1. Search Local Scraped Documents Database first
            logs.append(f"Searching local documents for entity and axis keywords...")
            local_docs = await search_local_documents(
                entity_name_en=entity.name_en,
                entity_name_ru=entity.name_ru,
                entity_name_he=entity.name_he,
                axis_name_en=axis.name_en,
                axis_name_ru=axis.name_ru,
                axis_name_he=axis.name_he,
                db=db,
                limit=5
            )
            
            scraped_texts = []
            for doc in local_docs:
                text = doc.content
                if not text and doc.file_path:
                    # Fallback file read
                    resolved_path = doc.file_path
                    if not resolved_path.startswith("/"):
                        for root_dir in ["/data/scraped_documents", "/data", "/app/data/scraped_documents"]:
                            cand = os.path.join(root_dir, resolved_path)
                            if os.path.exists(cand):
                                resolved_path = cand
                                break
                    if os.path.exists(resolved_path):
                        try:
                            with open(resolved_path, "r", encoding="utf-8") as f:
                                text = f.read()
                        except:
                            pass
                if text:
                    scraped_texts.append(text)
                    
            if scraped_texts:
                logs.append(f"Found {len(scraped_texts)} relevant local documents.")
            else:
                logs.append("No local documents matched. Falling back to Google PSE search...")
                # 2. Fallback: Google PSE Search
                # Generate search queries
                queries = await generate_search_queries(entity_name_en, axis_name_en)
                if not queries:
                    logs.append("Failed to generate search queries.")
                    continue
                    
                logs.append(f"Generated queries: {queries}")
                logs.append(f"Searching Google PSE for: '{queries[0]}'")
                urls = await search_google_pse(queries[0], max_results=3)
                logs.append(f"Found URLs: {urls}")
                
                for url in urls:
                    try:
                        file_path = await scrape_url(url, entity_id=entity_id)
                        logs.append(f"Successfully scraped: {url}")
                        
                        with open(file_path, "r", encoding="utf-8") as f:
                            file_content = f.read()
                            
                        file_content = file_content.replace("\x00", "").replace("\u0000", "")
                        lines = [l.strip() for l in file_content.split("\n") if l.strip()]
                        doc_title = lines[0].lstrip("#").strip().strip("*") if lines else "Scraped Article"
                        doc_title = doc_title.replace("\x00", "").replace("\u0000", "")
                        
                        new_doc = ScrapedDocument(
                            entity_id=entity_id,
                            axis_id=axis_id,
                            source_url=url,
                            file_path=file_path,
                            title=doc_title[:500],
                            content=file_content
                        )
                        db.add(new_doc)
                        await db.commit()
                        
                        scraped_texts.append(file_content)
                    except Exception as e:
                        logs.append(f"Failed to scrape {url}: {e}")
                        print(f"Failed to scrape {url}: {e}")
                        await db.rollback()
                        
            if not scraped_texts:
                logs.append("No texts found or successfully scraped. Skipping AI scoring.")
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
            
            score_val = ai_result.get("score")
            if score_val is None:
                score_val = 0.0
            else:
                try:
                    score_val = float(score_val)
                except:
                    score_val = 0.0

            confidence_val = ai_result.get("confidence")
            if confidence_val is None:
                confidence_val = 0.0
            else:
                try:
                    confidence_val = float(confidence_val)
                except:
                    confidence_val = 0.0

            just_en = ai_result.get("justification_en") or ""
            just_ru = ai_result.get("justification_ru") or ""
            just_he = ai_result.get("justification_he") or ""

            if existing_score:
                existing_score.score = score_val
                existing_score.confidence = confidence_val
                existing_score.justification_en = just_en
                existing_score.justification_ru = just_ru
                existing_score.justification_he = just_he
                await db.commit()
                await db.refresh(existing_score)
                results.append(existing_score)
                logs.append("Updated existing score in database.")
            else:
                new_score = EntityScore(
                    entity_id=entity_id,
                    axis_id=axis_id,
                    score=score_val,
                    confidence=confidence_val,
                    justification_en=just_en,
                    justification_ru=just_ru,
                    justification_he=just_he
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
        urls = await fetch_latest_news_rss(db=db, max_results=3)
        logs.append(f"Found generic political news URLs from RSS: {urls}")
        
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




