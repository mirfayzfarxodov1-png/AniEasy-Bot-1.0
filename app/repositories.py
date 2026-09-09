from datetime import datetime
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Anime, Episode, Favorite, User, WatchProgress

class UserRepository:
    def __init__(self, s: AsyncSession): self.s=s
    async def upsert(self, tg_id, username, first_name, is_admin=False):
        u=(await self.s.execute(select(User).where(User.telegram_id==tg_id))).scalar_one_or_none()
        if not u:
            u=User(telegram_id=tg_id, username=username, first_name=first_name, is_admin=is_admin); self.s.add(u)
        else:
            u.username=username; u.first_name=first_name; u.last_active=datetime.utcnow()
            # Environment/owner access can grant admin, but a DB-managed admin must not be
            # silently removed on every /start or callback.
            u.is_admin = bool(u.is_admin or is_admin)
        await self.s.commit(); return u

class AnimeRepository:
    def __init__(self,s): self.s=s
    async def create(self, **kw):
        a=Anime(**kw); self.s.add(a); await self.s.commit(); await self.s.refresh(a); return a
    async def get(self, aid): return (await self.s.execute(select(Anime).where(Anime.id==aid))).scalar_one_or_none()
    async def list(self, offset=0, limit=10): return (await self.s.execute(select(Anime).where(Anime.status!='deleted').order_by(Anime.created_at.desc()).offset(offset).limit(limit))).scalars().all()
    async def count(self): return (await self.s.execute(select(func.count()).select_from(Anime).where(Anime.status!='deleted'))).scalar_one()
    async def search(self,q,limit=20):
        p=f'%{q}%'; return (await self.s.execute(select(Anime).where(Anime.status!='deleted',or_(Anime.title.ilike(p),Anime.alternate_title.ilike(p),Anime.genre.ilike(p))).order_by(Anime.title).limit(limit))).scalars().all()
    async def save(self,a): await self.s.commit(); await self.s.refresh(a); return a
    async def delete(self,a): a.status='deleted'; await self.s.commit()

class EpisodeRepository:
    def __init__(self,s): self.s=s
    async def get(self,aid,num): return (await self.s.execute(select(Episode).where(Episode.anime_id==aid,Episode.episode_number==num))).scalar_one_or_none()
    async def list(self,aid,offset=0,limit=10): return (await self.s.execute(select(Episode).where(Episode.anime_id==aid).order_by(Episode.episode_number).offset(offset).limit(limit))).scalars().all()
    async def count(self,aid): return (await self.s.execute(select(func.count()).select_from(Episode).where(Episode.anime_id==aid))).scalar_one()
    async def add(self,**kw): e=Episode(**kw); self.s.add(e); await self.s.commit(); await self.s.refresh(e); return e
    async def delete(self,e): await self.s.delete(e); await self.s.commit()
    async def replace(self,e,**kw):
        for k,v in kw.items(): setattr(e,k,v)
        await self.s.commit(); await self.s.refresh(e); return e
    async def missing(self,aid):
        nums=(await self.s.execute(select(Episode.episode_number).where(Episode.anime_id==aid).order_by(Episode.episode_number))).scalars().all()
        return [n for n in range(1,max(nums or [0])+1) if n not in nums]

class FavoriteRepository:
    def __init__(self,s): self.s=s
    async def toggle(self,uid,aid):
        f=(await self.s.execute(select(Favorite).where(Favorite.user_id==uid,Favorite.anime_id==aid))).scalar_one_or_none()
        if f: await self.s.delete(f); added=False
        else: self.s.add(Favorite(user_id=uid,anime_id=aid)); added=True
        await self.s.commit(); return added
    async def list(self,uid): return (await self.s.execute(select(Anime).join(Favorite,Favorite.anime_id==Anime.id).where(Favorite.user_id==uid).order_by(Favorite.created_at.desc()))).scalars().all()

class ProgressRepository:
    def __init__(self,s): self.s=s
    async def set(self,uid,aid,num):
        p=(await self.s.execute(select(WatchProgress).where(WatchProgress.user_id==uid,WatchProgress.anime_id==aid))).scalar_one_or_none()
        if p: p.episode_number=num; p.updated_at=datetime.utcnow()
        else: self.s.add(WatchProgress(user_id=uid,anime_id=aid,episode_number=num))
        await self.s.commit()
