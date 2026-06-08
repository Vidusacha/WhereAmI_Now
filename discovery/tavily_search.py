import os
import time
import requests
from dotenv import load_dotenv
from utils.logger import setup_audit_logger

load_dotenv()
logger = setup_audit_logger(__name__)

def search_political_news():
    """
    Uses Tavily API to search for recent Israeli political statements and news.
    Returns a list of dictionaries with 'title', 'summary', and 'source'.
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        logger.warning("TAVILY_API_KEY not set. Skipping Tavily discovery.")
        return []

    logger.info("Starting targeted news search via Tavily API.")
    
    # We use targeted queries to pull high-density political statements
    queries = [
        "Latest political statements by Israeli politicians today",
        "Recent quotes and announcements by Israeli political parties"
    ]
    
    all_results = []
    headers = {"Content-Type": "application/json"}
    
    for query in queries:
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": False,
            "include_images": False,
            "include_raw_content": False,
            "max_results": 10,
            "days": 1 # we only want today's news
        }
        
        try:
            start_time = time.time()
            logger.debug(f"[API CALL START] Endpoint: POST https://api.tavily.com/search | Query: '{query}'")
            response = requests.post("https://api.tavily.com/search", json=payload, headers=headers)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                logger.debug(f"[API CALL END] Endpoint: Tavily API | Duration: {duration:.2f}s | Found: {len(results)} results")
                
                for item in results:
                    all_results.append({
                        "source": item.get("url", "tavily"),
                        "title": item.get("title", ""),
                        "summary": item.get("content", "")
                    })
            else:
                logger.error(f"Tavily API error: {response.status_code} - {response.text}")
                logger.debug(f"[API CALL END] Endpoint: Tavily API | Duration: {duration:.2f}s | Error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to query Tavily: {e}")

    # Remove exact duplicates based on URL
    unique_results = []
    seen_urls = set()
    for item in all_results:
        if item["source"] not in seen_urls:
            unique_results.append(item)
            seen_urls.add(item["source"])

    logger.info(f"Tavily search yielded {len(unique_results)} unique articles.")
    return unique_results
