from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

# During local dev, we might use a different URL or standard postgresql+asyncpg
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://admin:securepassword123@localhost:5432/whereami_db")

engine = create_async_engine(DATABASE_URL, echo=False)

async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with async_session_maker() as session:
        yield session
