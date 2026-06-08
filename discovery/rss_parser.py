import feedparser
import logging
import json
import google.generativeai as genai
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from utils.logger import setup_audit_logger

load_dotenv()

logger = setup_audit_logger(__name__)

def discover_rss_feeds():
    """
    Dynamically discovers Israeli news RSS feeds using Gemini API.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set. Using fallback RSS feeds.")
        return [
            "http://www.ynet.co.il/Integration/StoryRss2.xml",
            "https://www.haaretz.co.il/cmlink/1.1479262",
            "https://www.kan.org.il/rss/"
        ]

    try:
        genai.configure(api_key=api_key)
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        model = genai.GenerativeModel(model_name)
        prompt = (
            "Provide exactly 5 to 7 popular Israeli news RSS feed URLs. "
            "Ensure the list includes sources in Hebrew, English (e.g., Jerusalem Post, Times of Israel), "
            "and Russian (e.g., Newsru.co.il, Vesty.co.il). "
            "Return ONLY a valid JSON array of URLs like [\"http://...\"]. No markdown formatting or backticks."
        )
        
        start_time = time.time()
        logger.debug(f"[API CALL START] Endpoint: Gemini API (google.generativeai.generate_content) | Model: {model_name} | Prompt:\n{prompt}")
        response = model.generate_content(prompt)
        duration = time.time() - start_time
        logger.debug(f"[API CALL END] Endpoint: Gemini API | Duration: {duration:.2f}s | Response:\n{response.text}")
        
        text = response.text.replace('```json', '').replace('```', '').strip()
        feeds = json.loads(text)
        if isinstance(feeds, list) and len(feeds) > 0:
            logger.info(f"Dynamically discovered {len(feeds)} RSS feeds.")
            return feeds
    except Exception as e:
        logger.error(f"Failed to dynamically discover RSS feeds via Gemini: {e}")
        
    return []

def fetch_daily_news():
    """
    Fetches news from dynamically discovered Israeli RSS feeds.
    Returns a tuple of (all_items, len(feeds)).
    """
    logger.info("Starting daily news aggregation via RSS.")
    
    feeds = discover_rss_feeds()
    if not feeds:
        logger.warning("Could not discover any RSS feeds.")
        return [], 0

    all_items = []
    
    for feed_url in feeds:
        try:
            logger.info(f"Fetching from: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:15]: # Limit to top 15 per source for now
                all_items.append({
                    "source": feed_url,
                    "title": getattr(entry, "title", ""),
                    "summary": getattr(entry, "summary", ""),
                    "link": getattr(entry, "link", ""),
                    "pub_date": getattr(entry, "published", datetime.now().isoformat())
                })
        except Exception as e:
            logger.error(f"Failed to fetch from {feed_url}: {e}")
            
    logger.info(f"Aggregated {len(all_items)} articles.")
    return all_items, len(feeds)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    news, feed_count = fetch_daily_news()
    for n in news[:3]:
        print(n)
