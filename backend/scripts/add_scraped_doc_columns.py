import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://admin:securepassword123@postgres:5432/whereami_db")

async def migrate():
    print("Connecting to database...")
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        print("Adding 'title' and 'content' columns to scraped_documents table if they don't exist...")
        await conn.execute(text("ALTER TABLE scraped_documents ADD COLUMN IF NOT EXISTS title TEXT;"))
        await conn.execute(text("ALTER TABLE scraped_documents ADD COLUMN IF NOT EXISTS content TEXT;"))
        print("Database schema updated successfully.")

    # Now let's query all documents that need backfilling
    from database import async_session_maker
    from models import ScrapedDocument
    from sqlalchemy import select
    
    async with async_session_maker() as session:
        # We can query using sqlalchemy now since columns are added!
        query = select(ScrapedDocument).where(
            (ScrapedDocument.content == None) | (ScrapedDocument.title == None)
        )
        result = await session.execute(query)
        docs = result.scalars().all()
        
        print(f"Found {len(docs)} documents to backfill.")
        
        backfilled_count = 0
        failed_count = 0
        
        for idx, doc in enumerate(docs):
            path = doc.file_path
            
            # Resolve path
            resolved_path = path
            if not path.startswith("/"):
                # Relative path. Let's try different potential root directories:
                # 1. /data/scraped_documents/
                # 2. /data/
                # 3. /app/data/scraped_documents/
                candidates = [
                    os.path.join("/data/scraped_documents", path),
                    os.path.join("/data", path),
                    os.path.join("/app/data/scraped_documents", path),
                ]
                for cand in candidates:
                    if os.path.exists(cand):
                        resolved_path = cand
                        break
            
            if not os.path.exists(resolved_path):
                print(f"[{idx+1}/{len(docs)}] File not found: {path} (Resolved: {resolved_path})")
                failed_count += 1
                continue
                
            try:
                with open(resolved_path, "r", encoding="utf-8") as f:
                    file_content = f.read()
                
                # Replace NULL bytes to prevent PostgreSQL encoding errors
                file_content = file_content.replace("\x00", "").replace("\u0000", "")
                
                # Extract title: find the first non-empty line
                lines = [l.strip() for l in file_content.split("\n") if l.strip()]
                extracted_title = ""
                if lines:
                    # Clean markdown markers from title (e.g. # title, **title**)
                    extracted_title = lines[0].lstrip("#").strip().strip("*")
                
                if not extracted_title:
                    extracted_title = "Untitled Document"
                
                extracted_title = extracted_title.replace("\x00", "").replace("\u0000", "")
                    
                doc.title = extracted_title[:500] # limit title length just in case
                doc.content = file_content
                
                backfilled_count += 1
                if backfilled_count % 100 == 0:
                    print(f"Processed {backfilled_count} documents...")
                    await session.commit()
                    
            except Exception as e:
                print(f"Error reading file {resolved_path}: {e}")
                failed_count += 1
                
        await session.commit()
        print(f"Backfill complete: successfully backfilled {backfilled_count} documents, failed/skipped {failed_count}.")

if __name__ == "__main__":
    asyncio.run(migrate())
