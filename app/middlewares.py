import time
from collections import defaultdict
from aiogram import BaseMiddleware
from typing import Any, Awaitable, Callable

class DependenciesMiddleware(BaseMiddleware):
    def __init__(self, db, settings): self.db=db; self.settings=settings
    async def __call__(self, handler, event, data):
        async with self.db.session_factory() as session:
            data['db']=type('DB',(),{})(); data['db'].session=session
            data['db'].user=__import__('app.repositories',fromlist=['UserRepository']).UserRepository(session)
            data['db'].anime=__import__('app.repositories',fromlist=['AnimeRepository']).AnimeRepository(session)
            data['db'].episodes=__import__('app.repositories',fromlist=['EpisodeRepository']).EpisodeRepository(session)
            data['db'].fav=__import__('app.repositories',fromlist=['FavoriteRepository']).FavoriteRepository(session)
            data['settings']=self.settings
            data['db'].commit=session.commit
            return await handler(event,data)

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, seconds=0.7): self.seconds=seconds; self.last=defaultdict(float)
    async def __call__(self,handler,event,data):
        uid=getattr(getattr(event,'from_user',None),'id',0); now=time.monotonic()
        if uid and now-self.last[uid]<self.seconds:
            if hasattr(event,'answer'): await event.answer('⏳ Biroz kuting.')
            return
        self.last[uid]=now
        return await handler(event,data)
