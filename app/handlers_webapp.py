import json
from aiogram import Router
from aiogram.types import Message
from sqlalchemy import select
from .models import Anime, Episode
from .keyboards import anime_actions, inline_home

router = Router()

@router.message(lambda m: m.web_app_data is not None)
async def mini_app_action(message: Message, db, settings):
    raw = message.web_app_data.data or '{}'
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {'action': raw}
    action = str(data.get('action', '')).strip().lower()
    if action == 'watch_latest':
        row = (await db.session.execute(
            select(Anime, Episode)
            .join(Episode, Episode.anime_id == Anime.id)
            .where(Anime.status != 'deleted')
            .order_by(Episode.created_at.desc())
            .limit(1)
        )).first()
        if not row:
            return await message.answer('📺 Hozircha tomosha qilish uchun anime qismi mavjud emas.', reply_markup=inline_home())
        anime, episode = row
        await db.session.execute(select(Episode).where(Episode.id == episode.id))
        await message.answer_video(
            episode.telegram_file_id,
            caption=f'🎬 <b>{anime.title}</b>\n📺 {episode.episode_number}-qism\n\n🌐 AniEasy Mini App orqali tanlandi.',
            reply_markup=anime_actions(anime.id),
        )
        return
    if action == 'anime':
        items = await db.anime.list(0, settings.pagination_size)
        if not items:
            return await message.answer('📚 Katalog hozircha bo‘sh.', reply_markup=inline_home())
        rows = [[(f'🎬 {a.title}', f'anime:{a.id}')] for a in items]
        from .keyboards import ikb
        return await message.answer('📚 <b>AniEasy katalogi</b>\n\nAnime tanlang:', reply_markup=ikb(rows + [[('🏠 Bosh menyu', 'home')]]))
    if action == 'search':
        return await message.answer('🔎 Qidiruvni botdagi <b>Qidirish</b> tugmasi orqali boshlang.')
    if action == 'favorites':
        return await message.answer('⭐ Sevimlilar bo‘limi bot ichida ochiladi.')
    if action == 'continue':
        return await message.answer('▶️ Davom ettirish bo‘limi bot ichida ochiladi.')
    if action == 'latest':
        return await message.answer('🆕 Yangi qismlar bo‘limini bot ichida oching.')
    await message.answer('🌐 Mini App buyrug‘i qabul qilindi. Kerakli bo‘limni botdan davom ettiring.', reply_markup=inline_home())
