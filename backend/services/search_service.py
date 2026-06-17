import urllib.request
import json
import urllib.parse
import os
import aiohttp
import xml.etree.ElementTree as ET
from sqlalchemy import select
from models import StaticSource
from sqlalchemy.ext.asyncio import AsyncSession

async def fetch_latest_news_rss(db: AsyncSession, max_results: int = 5) -> list:
    """
    Fetches the latest news article URLs from RSS feeds stored in the database.
    Used for unsupervised axis discovery to guarantee fresh political context.
    """
    query = select(StaticSource).where(
        StaticSource.source_type == "rss",
        StaticSource.is_active == True
    )
    result = await db.execute(query)
    rss_sources = result.scalars().all()

    urls = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Disable SSL verification to support feeds with expired/self-signed certs (e.g. DEBKAfile)
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
        for source in rss_sources:
            feed_url = source.url
            try:
                async with session.get(feed_url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        root = ET.fromstring(content)
                        # Parse standard RSS <item> tags
                        for item in root.findall('.//item'):
                            link = item.find('link')
                            if link is not None and link.text:
                                urls.append(link.text)
                                if len(urls) >= max_results:
                                    return urls
            except Exception as e:
                print(f"Error fetching RSS {feed_url}: {e}")
                
    return urls

async def search_google_pse(query: str, max_results: int = 3) -> list:
    """
    Executes a web search using Google Programmable Search Engine (PSE).
    Requires GOOGLE_API_KEY and GOOGLE_PSE_ID in environment variables.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    pse_id = os.getenv("GOOGLE_PSE_ID")
    
    if not api_key or not pse_id:
        print("Warning: Google API keys not found. Search may return empty results.")
        return []
        
    url = f"https://www.googleapis.com/customsearch/v1?q={urllib.parse.quote(query)}&key={api_key}&cx={pse_id}&num={max_results}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get("items", [])
                    return [item.get("link") for item in items if "link" in item]
                else:
                    print(f"Google PSE error: HTTP {response.status}")
    except Exception as e:
        print(f"Error during Google PSE search for '{query}': {e}")
        
    return []

from typing import List
from models import ScrapedDocument
import re

async def search_local_documents(
    entity_name_en: str,
    entity_name_ru: str,
    entity_name_he: str,
    axis_name_en: str,
    axis_name_ru: str,
    axis_name_he: str,
    db: AsyncSession,
    limit: int = 5
) -> List[ScrapedDocument]:
    """
    Searches the local scraped_documents table in PostgreSQL for keywords matching
    the political entity and axis.
    Matches documents containing at least one entity term AND at least one axis term.
    """
    entity_terms = [t for t in [entity_name_en, entity_name_ru, entity_name_he] if t]
    axis_terms = [t for t in [axis_name_en, axis_name_ru, axis_name_he] if t]
    
    axis_terms = list(set(axis_terms))
    
    if not entity_terms or not axis_terms:
        return []
        
    from sqlalchemy import or_, and_
    
    entity_clauses = [ScrapedDocument.content.ilike(f"%{term}%") for term in entity_terms]
    axis_clauses = [ScrapedDocument.content.ilike(f"%{term}%") for term in axis_terms]
    
    entity_title_clauses = [ScrapedDocument.title.ilike(f"%{term}%") for term in entity_terms]
    axis_title_clauses = [ScrapedDocument.title.ilike(f"%{term}%") for term in axis_terms]
    
    query = select(ScrapedDocument).where(
        and_(
            or_(*entity_clauses, *entity_title_clauses),
            or_(*axis_clauses, *axis_title_clauses)
        )
    ).order_by(ScrapedDocument.scraped_at.desc()).limit(limit)
    
    result = await db.execute(query)
    matching_docs = result.scalars().all()
    
    print(f"Local search found {len(matching_docs)} documents matching entity {entity_name_en} and axis {axis_name_en}")
    return list(matching_docs)
