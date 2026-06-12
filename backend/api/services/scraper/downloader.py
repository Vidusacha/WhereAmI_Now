import os
import requests
import re
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from urllib.parse import urlparse

def download_and_extract(url: str, save_directory: str) -> str | None:
    """
    Downloads an HTML page, extracts its main text content as Markdown,
    and saves it to the specified directory.
    Returns the file path if successful, otherwise None.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Simple extraction using BeautifulSoup + Markdownify
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.extract()
            
        # Try to find a main content container, fallback to body
        main_content = soup.find('main') or soup.find('article') or soup.body
        if not main_content:
            main_content = soup # last resort
            
        markdown_content = md(str(main_content), strip=['a', 'img']).strip()
        
        if not markdown_content or len(markdown_content) < 50:
            print(f"Content from {url} is too short or empty. Skipping.")
            return None
            
        # Add source URL at the top
        final_content = f"Source: {url}\n\n{markdown_content}"
        
        # Create a safe filename from the URL
        parsed = urlparse(url)
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', parsed.netloc + parsed.path)
        safe_name = safe_name.strip('_')[:100] + ".md"
        
        os.makedirs(save_directory, exist_ok=True)
        file_path = os.path.join(save_directory, safe_name)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
            
        return file_path
        
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None
