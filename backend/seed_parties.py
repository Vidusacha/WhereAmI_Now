import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import sys

# Add the current directory to sys.path so we can import api.models
sys.path.append(os.path.dirname(__file__))

from models import Base, EntityType, PoliticalEntity, ApprovalStatus, StaticSource

DATABASE_URL = "postgresql+asyncpg://admin:securepassword123@postgres:5432/whereami_db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def seed_data():
    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Seed Entity Types
        party_type = await session.get(EntityType, "party")
        if not party_type:
            party_type = EntityType(
                id="party",
                name_en="Political Party",
                name_ru="Политическая партия",
                name_he="מפלגה פוליטית"
            )
            session.add(party_type)
        
        list_type = await session.get(EntityType, "list")
        if not list_type:
            list_type = EntityType(
                id="list",
                name_en="Electoral List",
                name_ru="Избирательный список",
                name_he="רשימה"
            )
            session.add(list_type)
            
        await session.commit()

        # List of parties to seed (with ballot letters and chairpersons)
        parties = [
            {"id": "likud", "en": "Likud", "ru": "Ликуд", "he": "הליכוד", "type": "party", "letters": "מחל", "chairperson": "Binyamin Netanyahu"},
            {"id": "yesh_atid", "en": "Yesh Atid", "ru": "Еш Атид", "he": "יש עתיד", "type": "party", "letters": "פה", "chairperson": "Yair Lapid"},
            {"id": "shas", "en": "Shas", "ru": "ШАС", "he": "ש\"ס", "type": "party", "letters": "שס", "chairperson": "Aryeh Deri"},
            {"id": "national_unity", "en": "National Unity", "ru": "Ха-Махане ха-мамлахти", "he": "המחנה הממלכתי", "type": "list", "letters": "כן", "chairperson": "Benny Gantz"},
            {"id": "religious_zionist", "en": "Religious Zionist Party", "ru": "Религиозный сионизм", "he": "הציונות הדתית", "type": "party", "letters": "ט", "chairperson": "Bezalel Smotrich"},
            {"id": "utj", "en": "United Torah Judaism", "ru": "Яхадут ха-Тора", "he": "יהדות התורה", "type": "list", "letters": "ג", "chairperson": "Yitzhak Goldknopf"},
            {"id": "otzma_yehudit", "en": "Otzma Yehudit", "ru": "Оцма Йехудит", "he": "עוצמה יהודית", "type": "party", "letters": "עץ", "chairperson": "Itamar Ben-Gvir"},
            {"id": "yisrael_beiteinu", "en": "Yisrael Beiteinu", "ru": "НДИ (Наш дом Израиль)", "he": "ישראל ביתנו", "type": "party", "letters": "ל", "chairperson": "Avigdor Lieberman"},
            {"id": "raam", "en": "Ra'am (UAL)", "ru": "РААМ", "he": "רע\"מ", "type": "party", "letters": "עם", "chairperson": "Mansour Abbas"},
            {"id": "hadash_taal", "en": "Hadash-Ta'al", "ru": "Хадаш-Тааль", "he": "חד\"ש-תע\"ל", "type": "list", "letters": "ום", "chairperson": "Ayman Odeh"},
            {"id": "democrats", "en": "The Democrats (Labor-Meretz)", "ru": "Демократы (Авода-Мерец)", "he": "הדמוקרטים", "type": "party", "letters": "אמת", "chairperson": "Yair Golan"},
            {"id": "noam", "en": "Noam", "ru": "Ноам", "he": "נעם", "type": "party", "letters": "ב", "chairperson": "Avi Maoz"},
            {"id": "balad", "en": "Balad", "ru": "Балад", "he": "בל\"ד", "type": "party", "letters": "ד", "chairperson": "Sami Abu Shehadeh"},
        ]

        for p in parties:
            entity = await session.get(PoliticalEntity, p["id"])
            if not entity:
                entity = PoliticalEntity(
                    id=p["id"],
                    name_en=p["en"],
                    name_ru=p["ru"],
                    name_he=p["he"],
                    entity_type_id=p["type"],
                    ballot_letters=p.get("letters"),
                    chairperson=p.get("chairperson"),
                    status=ApprovalStatus.APPROVED,
                    local_storage_folder=f"/data/entities/{p['id']}"
                )
                session.add(entity)
            else:
                # Update existing records with the new fields
                entity.ballot_letters = p.get("letters")
                entity.chairperson = p.get("chairperson")
        
        await session.commit()
        print("Successfully seeded initial political parties!")

        # Seed static sources
        from sqlalchemy import select
        sources = [
            {"url": "https://en.wikipedia.org/wiki/List_of_political_parties_in_Israel", "desc": "Wikipedia EN: List of parties"},
            {"url": "https://he.wikipedia.org/wiki/%D7%9E%D7%A4%D7%9C%D7%92%D7%95%D7%AA_%D7%91%D7%99%D7%A9%D7%A8%D7%90%D7%9C", "desc": "Wikipedia HE: List of parties"},
            {"url": "https://govil.ai/datasets/ebec1eda-e114-4f2e-b5fb-9766d10b890d/", "desc": "Govil AI Dataset for Elections"},
            {"url": "https://www.idi.org.il/policy/parties-and-elections/", "desc": "Israel Democracy Institute: Parties and Elections"}
        ]

        for s in sources:
            query = select(StaticSource).where(StaticSource.url == s["url"])
            result = await session.execute(query)
            existing = result.scalar_one_or_none()
            if not existing:
                new_src = StaticSource(url=s["url"], description=s["desc"])
                session.add(new_src)
        
        await session.commit()
        print("Successfully seeded static sources!")

if __name__ == "__main__":
    asyncio.run(seed_data())
