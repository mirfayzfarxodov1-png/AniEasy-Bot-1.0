import re
from sqlalchemy.ext.asyncio import AsyncSession
from .repositories import AnimeRepository, EpisodeRepository, FavoriteRepository, ProgressRepository

def parse_episode(text: str | None) -> int | None:
    if not text: return None
    m=re.search(r'(?<!\d)(\d{1,5})\s*(?:-?\s*qism|episode|ep)?(?!\d)', text, re.I)
    return int(m.group(1)) if m else None

class AnimeService:
    def __init__(self,s:AsyncSession): self.an=AnimeRepository(s); self.ep=EpisodeRepository(s); self.fav=FavoriteRepository(s); self.prog=ProgressRepository(s)
    async def create(self,title): return await self.an.create(title=title)
    async def save_episode(self, anime_id, number, file_id, unique_id, caption):
        old=await self.ep.get(anime_id,number)
        if old: return None, old
        return await self.ep.add(anime_id=anime_id,episode_number=number,telegram_file_id=file_id,file_unique_id=unique_id,caption=caption), None
    async def replace_episode(self,old,file_id,unique_id,caption): return await self.ep.replace(old,telegram_file_id=file_id,file_unique_id=unique_id,caption=caption)
