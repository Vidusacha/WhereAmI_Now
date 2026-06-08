import feedparser
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Default RSS feeds for Israeli news (example URLs)
FEEDS = {
    "Ynet": "http://www.ynet.co.il/Integration/StoryRss2.xml",
    "Haaretz": "https://www.haaretz.co.il/cmlink/1.1479262",
    "Kan 11": "https://www.kan.org.il/rss/"
}

def fetch_daily_news():
    """
    Fetches news from standard Israeli RSS feeds.
    Returns a list of dictionaries containing title, summary, link, and pub_date.
    """
    logger.info("Starting daily news aggregation via RSS.")
    articles = []
    
    for source, url in FEEDS.items():
        try:
            logger.info(f"Fetching from {source}: {url}")
            feed = feedparser.parse(url)
            
            for entry in feed.entries[:15]: # Limit to top 15 per source for now
                articles.append({
                    "source": source,
                    "title": getattr(entry, "title", ""),
                    "summary": getattr(entry, "summary", ""),
                    "link": getattr(entry, "link", ""),
                    "pub_date": getattr(entry, "published", datetime.now().isoformat())
                })
        except Exception as e:
            logger.error(f"Error parsing feed {source}: {e}")
            
    logger.info(f"Aggregated {len(articles)} articles.")
    return articles

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    news = fetch_daily_news()
    for n in news[:3]:
        print(n)
