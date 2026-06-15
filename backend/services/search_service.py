import urllib.request
import json
import urllib.parse
from duckduckgo_search import DDGS
import time
import asyncio

def _search_wikipedia(query: str, max_results: int = 3):
    url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&utf8=&format=json"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            results = data.get('query', {}).get('search', [])
            return [f"https://en.wikipedia.org/wiki/{urllib.parse.quote(item['title'].replace(' ', '_'))}" for item in results[:max_results]]
    except Exception as e:
        print(f"Wiki search failed: {e}")
        return []

async def search_duckduckgo(query: str, max_results: int = 3):
    """
    Executes a web search using DuckDuckGo without requiring API keys.
    Falls back to Wikipedia if DuckDuckGo fails or returns empty.
    Returns a list of URLs.
    """
    urls = []
    try:
        # DDGS is synchronous, so we run it in a thread pool executor
        def _sync_search():
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append(r.get("href"))
            return results
            
        loop = asyncio.get_running_loop()
        urls = await loop.run_in_executor(None, _sync_search)
        
    except Exception as e:
        print(f"Error during DuckDuckGo search for '{query}': {e}")
        
    if not urls:
        print(f"DuckDuckGo returned no results for '{query}'. Falling back to Wikipedia.")
        loop = asyncio.get_running_loop()
        urls = await loop.run_in_executor(None, _search_wikipedia, query, max_results)
        
    return urls
