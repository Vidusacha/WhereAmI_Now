import asyncio
import os
import sys
import uuid
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime

# Add the parent directory to sys.path so we can import models, database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import async_session_maker
from models import StaticSource, ScrapedDocument
from services.scraper_service import cascade_scrape
from sqlalchemy import select

async def scrape_all_rss():
    print("Starting global RSS scraping job...")
    async with async_session_maker() as session:
        # Get active RSS sources
        query = select(StaticSource).where(
            StaticSource.source_type == "rss",
            StaticSource.is_active == True
        )
        result = await session.execute(query)
        active_feeds = result.scalars().all()
        
        print(f"Found {len(active_feeds)} active RSS feeds to scrape.\n")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        connector = aiohttp.TCPConnector(ssl=False)
        
        async with aiohttp.ClientSession(headers=headers, connector=connector) as http_session:
            for idx, source in enumerate(active_feeds):
                print(f"[{idx+1}/{len(active_feeds)}] Scraping Feed: {source.description}")
                print(f"  URL: {source.url}")
                try:
                    # 1. Fetch XML
                    async with http_session.get(source.url, timeout=10) as response:
                        if response.status != 200:
                            print(f"  Error: HTTP {response.status}")
                            continue
                        content = await response.text()
                        
                    # 2. Parse XML
                    try:
                        root = ET.fromstring(content.encode('utf-8'))
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
                        
                        # Check if already scraped in database
                        chk_query = select(ScrapedDocument).where(ScrapedDocument.source_url == url)
                        chk_result = await session.execute(chk_query)
                        if chk_result.scalar_one_or_none():
                            skipped_count += 1
                            continue
                            
                        # 3. Scrape article content
                        try:
                            # Fetch and convert html to markdown
                            markdown_content = await cascade_scrape(url)
                            
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
                                scraped_at=datetime.utcnow()
                            )
                            session.add(new_doc)
                            scraped_count += 1
                            
                        except Exception as e:
                            print(f"    Failed to scrape article {url}: {e}")
                            
                    await session.commit()
                    print(f"  Done: Scraped {scraped_count} new articles, skipped {skipped_count} existing ones.\n")
                    
                    # Update last_scraped_at for the source
                    source.last_scraped_at = datetime.utcnow()
                    await session.commit()
                    
                except Exception as e:
                    print(f"  Error processing feed {source.description}: {e}\n")

if __name__ == "__main__":
    asyncio.run(scrape_all_rss())
