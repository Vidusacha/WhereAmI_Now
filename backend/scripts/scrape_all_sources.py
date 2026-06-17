import asyncio
import os
import sys
import uuid
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup

# Add the parent directory to sys.path so we can import models, database, etc.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import async_session_maker
from models import StaticSource, ScrapedDocument
from services.scraper_service import cascade_scrape
from sqlalchemy import select

async def scrape_all_sources():
    print("Starting global sources scraping job (RSS + Static)...")
    async with async_session_maker() as session:
        # Get active sources
        query = select(StaticSource).where(StaticSource.is_active == True)
        result = await session.execute(query)
        active_sources = result.scalars().all()
        
        print(f"Found {len(active_sources)} active sources to scrape.\n")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        connector = aiohttp.TCPConnector(ssl=False)
        
        async with aiohttp.ClientSession(headers=headers, connector=connector) as http_session:
            for idx, source in enumerate(active_sources):
                print(f"[{idx+1}/{len(active_sources)}] Scraping [{source.source_type.upper()}] {source.description}")
                print(f"  URL: {source.url}")
                
                try:
                    if source.source_type == "rss":
                        # --- Process RSS Feed ---
                        # 1. Fetch XML
                        async with http_session.get(source.url, timeout=15) as response:
                            if response.status != 200:
                                print(f"  Error: HTTP {response.status}")
                                continue
                            content_xml = await response.text()
                            
                        # 2. Parse XML
                        try:
                            root = ET.fromstring(content_xml.encode('utf-8'))
                            items = root.findall('.//item')
                        except Exception as pe:
                            print(f"  Error parsing XML: {pe}")
                            continue
                            
                        print(f"  Found {len(items)} article links in feed.")
                        
                        scraped_count = 0
                        skipped_count = 0
                        
                        # Limit to top 15 articles per feed on each run to manage load
                        for item in items[:15]:
                            link_node = item.find('link')
                            if link_node is None or not link_node.text:
                                continue
                            url = link_node.text.strip()
                            
                            title_node = item.find('title')
                            item_title = title_node.text.strip() if title_node is not None and title_node.text else ""
                            
                            # Check if already scraped in database
                            chk_query = select(ScrapedDocument).where(ScrapedDocument.source_url == url)
                            chk_result = await session.execute(chk_query)
                            if chk_result.scalar_one_or_none():
                                skipped_count += 1
                                continue
                                
                            # 3. Scrape article content
                            try:
                                markdown_content = await cascade_scrape(url)
                                
                                # Strip null bytes to prevent DB encoding errors
                                markdown_content = markdown_content.replace("\x00", "").replace("\u0000", "")
                                
                                if not item_title:
                                    # Fallback to first line of markdown
                                    lines = [l.strip() for l in markdown_content.split("\n") if l.strip()]
                                    item_title = lines[0].lstrip("#").strip().strip("*") if lines else "Untitled Article"
                                
                                item_title = item_title.replace("\x00", "").replace("\u0000", "")
                                
                                # 4. Save to file
                                dir_path = f"/data/scraped_rss/{source.id}"
                                os.makedirs(dir_path, exist_ok=True)
                                file_name = f"{uuid.uuid4().hex}.md"
                                file_path = os.path.join(dir_path, file_name)
                                
                                with open(file_path, "w", encoding="utf-8") as f:
                                    f.write(markdown_content)
                                    
                                # 5. Record in database
                                new_doc = ScrapedDocument(
                                    static_source_id=source.id,
                                    source_url=url,
                                    file_path=file_path,
                                    title=item_title[:500],
                                    content=markdown_content,
                                    scraped_at=datetime.utcnow()
                                )
                                session.add(new_doc)
                                scraped_count += 1
                                
                            except Exception as e:
                                print(f"    Failed to scrape article {url}: {e}")
                                
                        await session.commit()
                        print(f"  Done: Scraped {scraped_count} new articles, skipped {skipped_count} existing ones.\n")
                        
                    else:
                        # --- Process Static Source ---
                        # 1. Scrape content
                        markdown_content = await cascade_scrape(source.url)
                        markdown_content = markdown_content.replace("\x00", "").replace("\u0000", "")
                        
                        # Get title from first line of markdown or netloc
                        lines = [l.strip() for l in markdown_content.split("\n") if l.strip()]
                        doc_title = lines[0].lstrip("#").strip().strip("*") if lines else source.description or "Static Webpage"
                        doc_title = doc_title.replace("\x00", "").replace("\u0000", "")
                        
                        # 2. Save to file
                        dir_path = "/data/scraped_static"
                        os.makedirs(dir_path, exist_ok=True)
                        file_name = f"{source.id}.md"
                        file_path = os.path.join(dir_path, file_name)
                        
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(markdown_content)
                            
                        # 3. Check if document already exists in DB
                        chk_query = select(ScrapedDocument).where(ScrapedDocument.source_url == source.url)
                        chk_result = await session.execute(chk_query)
                        existing_doc = chk_result.scalar_one_or_none()
                        
                        if existing_doc:
                            existing_doc.file_path = file_path
                            existing_doc.title = doc_title[:500]
                            existing_doc.content = markdown_content
                            existing_doc.scraped_at = datetime.utcnow()
                            print(f"  Updated existing static document in DB.")
                        else:
                            new_doc = ScrapedDocument(
                                static_source_id=source.id,
                                source_url=source.url,
                                file_path=file_path,
                                title=doc_title[:500],
                                content=markdown_content,
                                scraped_at=datetime.utcnow()
                            )
                            session.add(new_doc)
                            print(f"  Created new static document in DB.")
                            
                        await session.commit()
                        print("  Done.\n")
                        
                    # Update last_scraped_at for the source
                    source.last_scraped_at = datetime.utcnow()
                    await session.commit()
                    
                except Exception as e:
                    print(f"  Error processing source {source.description}: {e}\n")
                    await session.rollback()

if __name__ == "__main__":
    asyncio.run(scrape_all_sources())
