from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from .config import Settings
from .models import Base

class Database:
    def __init__(self, settings: Settings):
        self.engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        self.session_factory = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self):
        await self.engine.dispose()
