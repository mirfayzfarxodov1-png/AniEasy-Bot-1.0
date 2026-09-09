import time
from collections import defaultdict
from aiogram import BaseMiddleware

class DependenciesMiddleware(BaseMiddleware):
    def __init__(self, db, settings):
        self.db = db
        self.settings = settings

    async def __call__(self, handler, event, data):
        async with self.db.session_factory() as session:
            data['db'] = type('DB', (), {})()
            data['db'].session = session
            repos = __import__('app.repositories', fromlist=['UserRepository','AnimeRepository','EpisodeRepository','FavoriteRepository','ProgressRepository'])
            data['db'].user = repos.UserRepository(session)
            data['db'].anime = repos.AnimeRepository(session)
            data['db'].episodes = repos.EpisodeRepository(session)
            data['db'].fav = repos.FavoriteRepository(session)
            data['db'].progress = repos.ProgressRepository(session)
            data['db'].commit = session.commit
            data['settings'] = self.settings
            return await handler(event, data)

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, seconds=0.7):
        self.seconds = seconds
        self.last = defaultdict(float)

    async def __call__(self, handler, event, data):
        uid = getattr(getattr(event, 'from_user', None), 'id', 0)
        now = time.monotonic()
        if uid and now - self.last[uid] < self.seconds:
            if hasattr(event, 'answer'):
                await event.answer('⏳ Biroz kuting.')
            return
        self.last[uid] = now
        return await handler(event, data)
