from random import choice

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select

from .access import is_admin
from .keyboards import ikb, main_menu
from .models import Anime, Episode, WatchProgress
from .states import Request

router = Router()


def back_rows():
    return [[('🏠 Bosh menyu', 'home')]]


async def send_list(c: CallbackQuery, title: str, items):
    if not items:
        await c.message.edit_text(f'{title}\n\n📭 Hozircha ma’lumot yo‘q.', reply_markup=ikb(back_rows()))
        return
    await c.message.edit_text(title, reply_markup=ikb([[x] for x in items] + back_rows()))


async def top_rows(db, limit):
    return (await db.session.execute(
        select(Anime, func.coalesce(func.sum(Episode.views), 0).label('views'))
        .join(Episode, Episode.anime_id == Anime.id, isouter=True)
        .where(Anime.status != 'deleted')
        .group_by(Anime.id)
        .order_by(func.coalesce(func.sum(Episode.views), 0).desc(), Anime.created_at.desc())
        .limit(limit)
    )).all()


async def new_episode_rows(db, limit):
    return (await db.session.execute(
        select(Episode, Anime)
        .join(Anime, Anime.id == Episode.anime_id)
        .where(Anime.status != 'deleted')
        .order_by(Episode.created_at.desc())
        .limit(limit)
    )).all()


@router.message(F.text == '🔥 Top anime')
async def top_button(m: Message, db, settings):
    rows = await top_rows(db, settings.pagination_size)
    text = '🔥 <b>Top anime</b>\n\n' + ('📭 Hozircha anime yo‘q.' if not rows else '\n'.join(f'🏆 {a.title} — {views} ko‘rish' for a, views in rows))
    await m.answer(text, reply_markup=ikb([[ (f'🎬 {a.title}', f'anime:{a.id}') ] for a, _ in rows] + back_rows()))


@router.callback_query(F.data == 'top')
async def top_callback(c: CallbackQuery, db, settings):
    rows = await top_rows(db, settings.pagination_size)
    await send_list(c, '🔥 <b>Top anime</b>', [(f'🏆 {a.title} — {views} ko‘rish', f'anime:{a.id}') for a, views in rows])
    await c.answer()


@router.message(F.text == '🎲 Tasodifiy')
async def random_button(m: Message, db):
    items = await db.anime.list(0, 200)
    if not items:
        return await m.answer('🎲 Hozircha anime mavjud emas.')
    a = choice(items)
    await m.answer(f'🎲 <b>Tasodifiy tanlov</b>\n\n🎬 {a.title}', reply_markup=ikb([[('📺 Qismlarni ochish', f'episodes:{a.id}:0')], *back_rows()]))


@router.callback_query(F.data == 'random')
async def random_callback(c: CallbackQuery, db):
    items = await db.anime.list(0, 200)
    if not items:
        await c.answer('📭 Anime mavjud emas.', show_alert=True)
        return
    a = choice(items)
    await c.message.edit_text(f'🎲 <b>Tasodifiy tanlov</b>\n\n🎬 {a.title}', reply_markup=ikb([[('📺 Qismlar', f'episodes:{a.id}:0')], *back_rows()]))
    await c.answer()


@router.message(F.text == '📅 Yangi qismlar')
async def new_episodes_button(m: Message, db, settings):
    rows = await new_episode_rows(db, settings.pagination_size)
    text = '📅 <b>Yangi qismlar</b>\n\n' + ('📭 Hozircha yo‘q.' if not rows else '\n'.join(f'📺 {a.title} — {e.episode_number}-qism' for e, a in rows))
    await m.answer(text, reply_markup=ikb([[(f'▶️ {a.title} {e.episode_number}-qism', f'episode:{a.id}:{e.episode_number}')] for e, a in rows] + back_rows()))


@router.callback_query(F.data == 'new_eps')
async def new_episodes_callback(c: CallbackQuery, db, settings):
    rows = await new_episode_rows(db, settings.pagination_size)
    await send_list(c, '📅 <b>Yangi qismlar</b>', [(f'▶️ {a.title} — {e.episode_number}-qism', f'episode:{a.id}:{e.episode_number}') for e, a in rows])
    await c.answer()


@router.message(F.text == '📈 Trend')
async def trend_button(m: Message, db, settings):
    rows = await top_rows(db, min(10, settings.pagination_size))
    await m.answer('📈 <b>Trend</b>\n\n' + ('Ma’lumot yo‘q.' if not rows else '\n'.join(f'📊 {a.title} — {views} ko‘rish' for a, views in rows)), reply_markup=ikb([[ (f'🎬 {a.title}', f'anime:{a.id}') ] for a, _ in rows] + back_rows()))


@router.callback_query(F.data == 'trend')
async def trend_callback(c: CallbackQuery, db, settings):
    rows = await top_rows(db, min(10, settings.pagination_size))
    await send_list(c, '📈 <b>Trend</b>', [(f'📊 {a.title} — {views} ko‘rish', f'anime:{a.id}') for a, views in rows])
    await c.answer()


async def history_rows(db, uid):
    return (await db.session.execute(
        select(WatchProgress, Anime)
        .join(Anime, Anime.id == WatchProgress.anime_id)
        .where(WatchProgress.user_id == uid, Anime.status != 'deleted')
        .order_by(WatchProgress.updated_at.desc())
        .limit(20)
    )).all()


@router.message(F.text == '🕘 Tarix')
async def history_button(m: Message, db, settings):
    u = await db.user.upsert(m.from_user.id, m.from_user.username, m.from_user.first_name, is_admin(m.from_user.id, settings))
    rows = await history_rows(db, u.id)
    await m.answer('🕘 <b>Tarix</b>\n\n' + ('Hali tarix yo‘q.' if not rows else '\n'.join(f'🎬 {a.title} — {p.episode_number}-qism' for p, a in rows)), reply_markup=ikb([[(f'▶️ {a.title}', f'episode:{a.id}:{p.episode_number}')] for p, a in rows] + back_rows()))


@router.callback_query(F.data == 'history')
async def history_callback(c: CallbackQuery, db, settings):
    u = await db.user.upsert(c.from_user.id, c.from_user.username, c.from_user.first_name, is_admin(c.from_user.id, settings))
    rows = await history_rows(db, u.id)
    await send_list(c, '🕘 <b>Tarix</b>', [(f'▶️ {a.title} — {p.episode_number}-qism', f'episode:{a.id}:{p.episode_number}') for p, a in rows])
    await c.answer()


async def genre_values(db):
    values = (await db.session.execute(select(Anime.genre).where(Anime.genre.is_not(None), Anime.status != 'deleted'))).scalars().all()
    return sorted({g.strip() for value in values if value for g in value.split(',') if g.strip()})


@router.message(F.text == '🏷 Janr bo‘yicha')
@router.message(F.text == '🎭 Janrlar')
async def genres_button(m: Message, db, settings):
    genres = await genre_values(db)
    rows = [[(f'🏷 {g}', f'genre:{g}')] for g in genres]
    await m.answer('🏷 <b>Janrlar</b>\n\nJanrni tanlang:' if genres else '🏷 <b>Janrlar</b>\n\nHali janrlar kiritilmagan.', reply_markup=ikb(rows + back_rows()))


@router.callback_query(F.data == 'genres')
async def genres_callback(c: CallbackQuery, db):
    genres = await genre_values(db)
    await c.message.edit_text('🏷 <b>Janrlar</b>\n\nJanrni tanlang:' if genres else '🏷 <b>Janrlar</b>\n\nHali janrlar kiritilmagan.', reply_markup=ikb([[(f'🏷 {g}', f'genre:{g}')] for g in genres] + back_rows()))
    await c.answer()


@router.callback_query(F.data.startswith('genre:'))
async def genre_callback(c: CallbackQuery, db, settings):
    genre = c.data.split(':', 1)[1]
    items = await db.anime.search(genre, settings.pagination_size)
    await send_list(c, f'🏷 <b>{genre}</b>', [(f'🎬 {a.title}', f'anime:{a.id}') for a in items])
    await c.answer()


@router.message(F.text == '🌟 Premium')
async def premium(m: Message, settings):
    await m.answer('🌟 <b>Premium</b>\n\nHozircha barcha asosiy funksiyalar bepul.', reply_markup=main_menu(is_admin(m.from_user.id, settings)))


@router.callback_query(F.data == 'premium')
async def premium_callback(c: CallbackQuery):
    await c.message.edit_text('🌟 <b>Premium</b>\n\nHozircha barcha asosiy funksiyalar bepul.', reply_markup=ikb(back_rows()))
    await c.answer()


@router.message(F.text == '📌 Saqlangan')
async def saved_button(m: Message, db, settings):
    u = await db.user.upsert(m.from_user.id, m.from_user.username, m.from_user.first_name, is_admin(m.from_user.id, settings))
    favs = await db.fav.list(u.id)
    await m.answer('📌 <b>Saqlangan</b>\n\n' + ('📭 Bo‘sh.' if not favs else 'Sevimli anime:') , reply_markup=ikb([[(f'🎬 {a.title}', f'anime:{a.id}')] for a in favs] + back_rows()))


@router.message(F.text == '🎯 Tavsiyalar')
async def recommendations(m: Message, db, settings):
    u = await db.user.upsert(m.from_user.id, m.from_user.username, m.from_user.first_name, is_admin(m.from_user.id, settings))
    favs = await db.fav.list(u.id)
    favorite_ids = {a.id for a in favs}
    genres = [g.strip() for a in favs if a.genre for g in a.genre.split(',') if g.strip()]
    candidates = await db.anime.search(genres[0], settings.pagination_size) if genres else await db.anime.list(0, settings.pagination_size)
    items = [a for a in candidates if a.id not in favorite_ids]
    await m.answer('🎯 <b>Tavsiyalar</b>\n\n' + ('📭 Hozircha tavsiya yo‘q.' if not items else 'Sizga mos anime:'), reply_markup=ikb([[(f'🎯 {a.title}', f'anime:{a.id}')] for a in items] + back_rows()))


@router.callback_query(F.data == 'recommend')
async def recommend_callback(c: CallbackQuery, db, settings):
    u = await db.user.upsert(c.from_user.id, c.from_user.username, c.from_user.first_name, is_admin(c.from_user.id, settings))
    favs = await db.fav.list(u.id)
    favorite_ids = {a.id for a in favs}
    genres = [g.strip() for a in favs if a.genre for g in a.genre.split(',') if g.strip()]
    candidates = await db.anime.search(genres[0], settings.pagination_size) if genres else await db.anime.list(0, settings.pagination_size)
    await send_list(c, '🎯 <b>Tavsiyalar</b>', [(f'🎯 {a.title}', f'anime:{a.id}') for a in candidates if a.id not in favorite_ids])
    await c.answer()


@router.message(F.text == '📊 Bot statistikasi')
async def bot_stats(m: Message, db, settings):
    animes = await db.anime.count()
    episodes = (await db.session.execute(select(func.count()).select_from(Episode))).scalar_one()
    views = (await db.session.execute(select(func.coalesce(func.sum(Episode.views), 0)))).scalar_one()
    users = (await db.session.execute(select(func.count(func.distinct(WatchProgress.user_id))))).scalar_one()
    await m.answer(f'📊 <b>Bot statistikasi</b>\n\n🎬 Anime: {animes}\n📺 Qismlar: {episodes}\n👥 Tomosha qilganlar: {users}\n👁 Ko‘rishlar: {views}', reply_markup=main_menu(is_admin(m.from_user.id, settings)))


@router.callback_query(F.data == 'bot_stats')
async def bot_stats_callback(c: CallbackQuery, db):
    animes = (await db.session.execute(select(func.count()).select_from(Anime).where(Anime.status != 'deleted'))).scalar_one()
    episodes = (await db.session.execute(select(func.count()).select_from(Episode))).scalar_one()
    views = (await db.session.execute(select(func.coalesce(func.sum(Episode.views), 0)))).scalar_one()
    await c.message.edit_text(f'📊 <b>Bot statistikasi</b>\n\n🎬 Anime: {animes}\n📺 Qismlar: {episodes}\n👁 Ko‘rishlar: {views}', reply_markup=ikb(back_rows()))
    await c.answer()


@router.message(F.text == '📝 So‘rov')
@router.message(F.text == '📝 So‘rov yuborish')
async def request_start(m: Message, state: FSMContext):
    await state.set_state(Request.anime)
    await m.answer('📝 <b>Anime so‘rovi</b>\n\nKerakli anime nomini yuboring:')


@router.message(Request.anime)
async def request_finish(m: Message, state: FSMContext, bot, settings):
    title = (m.text or '').strip()
    if not title:
        return await m.answer('❌ Anime nomini matn ko‘rinishida yuboring.')
    if settings.owner_id:
        await bot.send_message(settings.owner_id, f'📝 <b>Yangi anime so‘rovi</b>\n\n👤 {m.from_user.full_name}\n🆔 <code>{m.from_user.id}</code>\n🎬 {title}')
    await state.clear()
    await m.answer('✅ So‘rovingiz administratorga yuborildi.', reply_markup=main_menu(is_admin(m.from_user.id, settings)))


@router.message(F.text == '💬 Aloqa')
async def contact(m: Message, settings):
    owner = f'<code>{settings.owner_id}</code>' if settings.owner_id else 'administrator'
    await m.answer(f'💬 <b>Aloqa</b>\n\nAdministrator: {owner}', reply_markup=main_menu(is_admin(m.from_user.id, settings)))


@router.callback_query(F.data == 'contact')
async def contact_callback(c: CallbackQuery, settings):
    owner = f'<code>{settings.owner_id}</code>' if settings.owner_id else 'administrator'
    await c.message.edit_text(f'💬 <b>Aloqa</b>\n\nAdministrator: {owner}', reply_markup=ikb(back_rows()))
    await c.answer()


INFO = {
    '🎨 Tema': '🎨 <b>Tema</b>\n\nAniEasy bot Telegram ilovangizning tema sozlamalaridan foydalanadi.',
    '📚 Qo‘llanma': '📚 <b>Qo‘llanma</b>\n\n1️⃣ Anime tanlang\n2️⃣ Qismlar bo‘limiga kiring\n3️⃣ Qismni bosing\n4️⃣ Keyingi/oldingi qism tugmalaridan foydalaning.',
    '🆘 Muammo': '🆘 <b>Muammo</b>\n\nVideo ochilmasa /start ni yuboring va qayta urinib ko‘ring.',
    '🆘 Muammo haqida': '🆘 <b>Muammo</b>\n\nVideo ochilmasa qayta urinib ko‘ring yoki administratorga xabar bering.',
    '🔔 Yangiliklar': '🔔 <b>Yangiliklar</b>\n\nYangi anime va qismlar shu bo‘limga tushadi.',
    '🔔 Yangiliklar obunasi': '🔔 <b>Yangiliklar obunasi</b>\n\nYangi postlarni kanal orqali kuzatishingiz mumkin.',
}


@router.message(F.text.in_(list(INFO.keys())))
async def info_menu(m: Message, settings):
    await m.answer(INFO[m.text], reply_markup=main_menu(is_admin(m.from_user.id, settings)))


@router.callback_query(F.data == 'quick')
async def quick_callback(c: CallbackQuery):
    await c.message.edit_text('⚡ <b>Tezkor menyu</b>\n\nKerakli bo‘limni tanlang:', reply_markup=ikb([
        [('🔥 Top anime', 'top'), ('🎲 Tasodifiy', 'random')],
        [('📅 Yangi qismlar', 'new_eps'), ('📈 Trend', 'trend')],
        [('⭐ Sevimlilar', 'favorites'), ('📺 Davom ettirish', 'continue')],
        [('🔎 Qidirish', 'search'), ('🎭 Janrlar', 'genres')],
        [('🏠 Bosh menyu', 'home')],
    ]))
    await c.answer()


@router.message(F.text == '⚡ Tezkor menyu')
async def quick_button(m: Message):
    await m.answer('⚡ <b>Tezkor menyu</b>\n\nKerakli bo‘limni tanlang:', reply_markup=ikb([
        [('🔥 Top anime', 'top'), ('🎲 Tasodifiy', 'random')],
        [('📅 Yangi qismlar', 'new_eps'), ('📈 Trend', 'trend')],
        [('⭐ Sevimlilar', 'favorites'), ('📺 Davom ettirish', 'continue')],
        [('🔎 Qidirish', 'search'), ('🎭 Janrlar', 'genres')],
        [('🏠 Bosh menyu', 'home')],
    ]))


@router.callback_query(F.data == 'theme')
async def theme_callback(c: CallbackQuery):
    await c.message.edit_text(INFO['🎨 Tema'], reply_markup=ikb(back_rows())); await c.answer()


@router.callback_query(F.data == 'guide')
async def guide_callback(c: CallbackQuery):
    await c.message.edit_text(INFO['📚 Qo‘llanma'], reply_markup=ikb(back_rows())); await c.answer()


@router.callback_query(F.data == 'problem')
async def problem_callback(c: CallbackQuery):
    await c.message.edit_text(INFO['🆘 Muammo'], reply_markup=ikb(back_rows())); await c.answer()


@router.callback_query(F.data == 'notify')
async def notify_callback(c: CallbackQuery):
    await c.message.edit_text(INFO['🔔 Yangiliklar'], reply_markup=ikb(back_rows())); await c.answer()
