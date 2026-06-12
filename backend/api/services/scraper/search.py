import os
from googleapiclient.discovery import build
from tavily import TavilyClient

def get_google_api_key():
    return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

def search_google_pse(query: str, num_results: int = 5) -> list[str]:
    """
    Searches Google Custom Search and returns a list of URLs.
    """
    api_key = get_google_api_key()
    cx = os.getenv("SEARCH_ENGINE_ID")
    
    if not api_key or not cx:
        print("Missing Google API Key or Search Engine ID for PSE")
        return []

    try:
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=query, cx=cx, num=num_results).execute()
        urls = []
        if 'items' in res:
            for item in res['items']:
                urls.append(item.get('link'))
        return urls
    except Exception as e:
        print(f"Google PSE Search error: {e}")
        return []

def search_tavily(query: str, num_results: int = 5) -> list[str]:
    """
    Searches Tavily API and returns a list of URLs.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("Missing Tavily API Key")
        return []

    try:
        tavily = TavilyClient(api_key=api_key)
        response = tavily.search(query=query, search_depth="basic", max_results=num_results)
        urls = []
        if 'results' in response:
            for item in response['results']:
                urls.append(item.get('url'))
        return urls
    except Exception as e:
        print(f"Tavily Search error: {e}")
        return []
