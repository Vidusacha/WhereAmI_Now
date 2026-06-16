import urllib.request
import json
import urllib.parse
import os
import aiohttp
import xml.etree.ElementTree as ET

# RSS Feeds for Unsupervised Discovery
RSS_FEEDS = [
    "https://www.timesofisrael.com/feed/",
    "https://www.jpost.com/Rss/RssFeedsHeadlines.aspx",
]

async def fetch_latest_news_rss(max_results: int = 5) -> list:
    """
    Fetches the latest news article URLs from predefined Israeli RSS feeds.
    Used for unsupervised axis discovery to guarantee fresh political context.
    """
    urls = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    async with aiohttp.ClientSession(headers=headers) as session:
        for feed_url in RSS_FEEDS:
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
