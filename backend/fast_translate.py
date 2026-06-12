import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from models import PoliticalEntity
from deep_translator import GoogleTranslator

DATABASE_URL = "postgresql+asyncpg://admin:securepassword123@postgres:5432/whereami_db"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def translate_all():
    async with async_session() as session:
        # Load existing names for deduplication
        existing_result = await session.execute(select(PoliticalEntity.name_en))
        existing_names = {row[0] for row in existing_result.all() if row[0]}
        
        # Select remaining items
        result = await session.execute(select(PoliticalEntity).where(PoliticalEntity.name_en.like('GovIL Party%')))
        entities = result.scalars().all()
        print(f"Translating {len(entities)} parties via deep-translator...")
        
        translator_en = GoogleTranslator(source='iw', target='en')
        translator_ru = GoogleTranslator(source='iw', target='ru')
        
        translated_count = 0
        for e in entities:
            try:
                en_name = translator_en.translate(e.name_he).strip()
                ru_name = translator_ru.translate(e.name_he).strip()
                
                # In-memory deduplication
                original_en = en_name
                counter = 1
                while en_name in existing_names:
                    en_name = f"{original_en} ({counter})"
                    counter += 1
                
                existing_names.add(en_name)
                
                e.name_en = en_name
                e.name_ru = ru_name
                translated_count += 1
                print(f"[{translated_count}/{len(entities)}] {e.name_he} -> {en_name} / {ru_name}")
                
            except Exception as ex:
                print(f"Error translating {e.name_he}: {ex}")
        
        await session.commit()
        print(f"Successfully translated and committed {translated_count} parties.")

if __name__ == "__main__":
    asyncio.run(translate_all())
