import feedparser
import logging
import json
import google.generativeai as genai
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

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
        model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        model = genai.GenerativeModel(model_name)
        prompt = (
            "Provide exactly 5 to 7 popular Israeli news RSS feed URLs. "
            "Ensure the list includes sources in Hebrew, English (e.g., Jerusalem Post, Times of Israel), "
            "and Russian (e.g., Newsru.co.il, Vesty.co.il). "
            "Return ONLY a valid JSON array of strings containing the URLs. Do not include markdown formatting or explanations."
        )
        response = model.generate_content(prompt)
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
    Returns a list of dictionaries containing title, summary, link, and pub_date.
    """
    logger.info("Starting daily news aggregation via RSS.")
    articles = []
    
    feed_urls = discover_rss_feeds()
    
    for url in feed_urls:
        try:
            logger.info(f"Fetching from: {url}")
            feed = feedparser.parse(url)
            
            for entry in feed.entries[:15]: # Limit to top 15 per source for now
                articles.append({
                    "source": url,
                    "title": getattr(entry, "title", ""),
                    "summary": getattr(entry, "summary", ""),
                    "link": getattr(entry, "link", ""),
                    "pub_date": getattr(entry, "published", datetime.now().isoformat())
                })
        except Exception as e:
            logger.error(f"Error parsing feed {url}: {e}")
            
    logger.info(f"Aggregated {len(articles)} articles.")
    return articles

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    news = fetch_daily_news()
    for n in news[:3]:
        print(n)
