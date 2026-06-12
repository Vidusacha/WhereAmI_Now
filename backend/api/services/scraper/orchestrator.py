import os
from .search import search_google_pse, search_tavily
from .downloader import download_and_extract

DATA_DIR = os.path.join(os.path.dirname(__file__), "../../../../data/scraped_documents")

def run_scraping_job(entity_id: str, entity_name_en: str, entity_name_he: str):
    """
    Runs the full scraping pipeline for a political entity.
    """
    print(f"Starting scraping job for {entity_name_en} ({entity_name_he})")
    
    # 1. Generate search queries
    # Look for official platforms, manifestos, or detailed wikipedia entries
    queries = [
        f"{entity_name_he} מצע", # Hebrew for "manifesto/platform"
        f"{entity_name_he} מפלגה אתר רשמי", # "party official website"
    ]
    
    all_urls = set()
    
    # 2. Search using APIs
    for q in queries:
        print(f"Searching for: {q}")
        
        # Try Google PSE
        g_urls = search_google_pse(q, num_results=3)
        all_urls.update(g_urls)
        
        # Try Tavily
        t_urls = search_tavily(q, num_results=3)
        all_urls.update(t_urls)
        
    print(f"Found {len(all_urls)} unique URLs to scrape.")
    
    # 3. Create target directory
    # Sanitize folder name
    safe_folder = "".join(c if c.isalnum() or c in " _-" else "_" for c in entity_name_en).strip()
    save_dir = os.path.join(DATA_DIR, safe_folder)
    os.makedirs(save_dir, exist_ok=True)
    
    # 4. Download and extract
    downloaded_files = []
    for url in all_urls:
        print(f"Downloading: {url}")
        file_path = download_and_extract(url, save_dir)
        if file_path:
            downloaded_files.append(file_path)
            
    print(f"Scraping job complete. Saved {len(downloaded_files)} documents to {save_dir}.")
    return downloaded_files
