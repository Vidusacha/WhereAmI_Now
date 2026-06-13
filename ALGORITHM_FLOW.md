# Project WhereAmI_Now: Algorithm Flow (V2 Scraping)

This document describes the exact step-by-step algorithm executed for the V2 Web Scraping Pipeline.
These steps correspond to the orchestrator logic inside ackend/api/services/scraper/orchestrator.py.

## Step 1: Triggering the Job
- The Flutter Admin UI sends a POST request to /api/documents/scrape/{entity_id}.
- FastAPI initializes a background task un_scraping_job to avoid blocking the UI, passing the entity_id and names (English and Hebrew).

## Step 2: Generating Search Queries
- The scraper automatically generates highly targeted search queries in Hebrew.
- Queries are formatted as [Party Name Hebrew] + "???" (manifesto) and [Party Name Hebrew] + "??? ????? ????" (official website).

## Step 3: Web Search APIs
- The pipeline executes searches across two distinct search engines simultaneously to maximize discovery:
  1. **Google Programmable Search Engine (PSE)**: Fetches the top 3 relevant results from indexed Google search.
  2. **Tavily Search API**: A specialized AI research search engine that fetches the top 3 contextually relevant results.
- All discovered URLs are deduplicated into a unique set.

## Step 4: Content Downloading & Extraction
- The orchestrator sanitizes the English party name to create a safe local directory name.
- For each unique URL:
  - The download_and_extract function is called.
  - HTML content is fetched via HTTP requests.
  - Content is parsed and converted to Markdown to strip away noisy web components.
  - The cleaned .md file is saved to the local host machine at data/scraped_documents/[Party_Name]/.

## Step 5: Database Persistence
- After the files are successfully written to the filesystem, the orchestrator connects to the PostgreSQL database.
- It iterates over the downloaded files and creates new ScrapedDocument entries in the DB.
- These DB entries store the entity_id, original source_url, and the relative ile_path.
- The UI can then immediately reflect the newly scraped documents by querying the API.
