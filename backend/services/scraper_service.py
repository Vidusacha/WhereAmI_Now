import aiohttp
from bs4 import BeautifulSoup
import markdownify

async def cascade_scrape(url: str) -> str:
    """
    Attempts to scrape the URL using aiohttp and convert to markdown.
    If it fails, raises an Exception so we don't pass error strings to the LLM.
    """
    print(f"Scraping: {url}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, timeout=10) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch: HTTP {response.status}")
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            # Remove scripts and styles
            for element in soup(["script", "style"]):
                element.extract()
            # Get text or convert to markdown
            text = markdownify.markdownify(str(soup), heading_style="ATX")
            if not text.strip():
                raise Exception("No content found on page.")
            return text[:10000] # Limit to 10k chars to avoid blowing up context

async def execute_pse_search(query: str) -> list:
    """
    Placeholder for Google Programmable Search Engine (PSE) query.
    Returns a list of URLs.
    """
    print(f"[STUB] Searching Google PSE for: {query}")
    return [
        "https://example.com/mock-article-1",
        "https://example.com/mock-article-2"
    ]

import os
import uuid

async def scrape_url(url: str, entity_id: str) -> str:
    """
    Scrapes the URL and saves it to a local file, returning the file path.
    """
    content = await cascade_scrape(url)
    
    # Ensure directory exists
    dir_path = f"/data/entities/{entity_id}/scraped"
    os.makedirs(dir_path, exist_ok=True)
    
    # Generate unique filename
    file_name = f"{uuid.uuid4().hex}.md"
    file_path = os.path.join(dir_path, file_name)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return file_path
