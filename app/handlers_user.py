from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import func, select
from .keyboards import main_menu, inline_home, ikb, episodes_page, episode_nav, anime_actions
from .states import Search
from .models import Episode, Anime, WatchProgress
from .access import is_admin

router = Router()


def home_text():
    return '🏠 <b>AniEasy Bot 1.0</b>\n\n🎬 Anime olami siz uchun tayyor!\nKerakli bo‘limni tanlang:'


async def send_home(m, settings, edit=False):
    admin = is_admin(m.from_user.id, settings)
    if edit:
        await m.edit_text(home_text(), reply_markup=inline_home(admin))
    else:
        await m.answer(home_text(), reply_markup=main_menu(admin))


@router.message(Command('help'))
@router.message(F.text == 'ℹ️ Yordam')
async def help_cmd(m: Message, settings):
    await m.answer(
        'ℹ️ <b>Yordam</b>\n\n'
        '🎬 Anime — katalog\n🔎 Qidirish — nomi, janri yoki muqobil nomi bo‘yicha\n'
        '⭐ Sevimlilar — saqlangan anime\n🆕 Yangiliklar — oxirgi qo‘shilganlar\n'
        '📺 Davom ettirish — oxirgi ko‘rilgan qism\n👤 Profil — akkaunt va faollik\n'
        '🎭 Janrlar — janr bo‘yicha tanlash',
        reply_markup=main_menu(is_admin(m.from_user.id, settings)),
    )


@router.message(F.text == '🏠 Bosh menyu')
async def home_button(m: Message, settings):
    await send_home(m, settings)


@router.message(F.text == '🎬 Anime')
async def anime_button(m: Message, db, settings):
    await show_anime(m, db, settings, 0)


@router.callback_query(F.data == 'anime')
async def anime_list(c: CallbackQuery, db, settings):
    await show_anime(c.message, db, settings, 0, True)
    await c.answer()


async def show_anime(m, db, settings, page=0, edit=False):
    size = settings.pagination_size
    items = await db.anime.list(page * size, size)
    if not items:
        text = '📭 Hozircha anime mavjud emas.'
        markup = inline_home(is_admin(m.from_user.id, settings))
    else:
        text = f'🎬 <b>Anime katalogi</b>\n\nSahifa: {page + 1}'
        rows = [[(f'🎬 {a.title}', f'anime:{a.id}')] for a in items]
        nav = []
        if page > 0:
            nav.append(('⬅️', f'anime_page:{page - 1}'))
        if len(items) == size:
            nav.append(('➡️', f'anime_page:{page + 1}'))
        if nav:
            rows.append(nav)
        rows.append([('🏠 Bosh menyu', 'home')])
        markup = ikb(rows)
    if edit:
        await m.edit_text(text, reply_markup=markup)
    else:
        await m.answer(text, reply_markup=markup)


@router.callback_query(F.data.startswith('anime_page:'))
async def anime_page(c: CallbackQuery, db, settings):
    try:
        page = max(0, int(c.data.split(':', 1)[1]))
    except (ValueError, IndexError):
        return await c.answer('❌ Sahifa xatosi.', show_alert=True)
    await show_anime(c.message, db, settings, page, True)
    await c.answer()


@router.callback_query(F.data.startswith('anime:'))
async def anime_detail(c: CallbackQuery, db, settings):
    try:
        aid = int(c.data.split(':', 1)[1])
    except (ValueError, IndexError):
        return await c.answer('❌ Anime ID xatosi.', show_alert=True)
    a = await db.anime.get(aid)
    if not a or a.status == 'deleted':
        return await c.answer('Anime topilmadi.', show_alert=True)
    n = await db.episodes.count(aid)
    u = await db.user.upsert(c.from_user.id, c.from_user.username, c.from_user.first_name, is_admin(c.from_user.id, settings))
    favs = await db.fav.list(u.id)
    favorite = any(x.id == aid for x in favs)
    text = f'🎬 <b>{a.title}</b>\n📺 Qismlar: {n}'
    if a.genre:
        text += f'\n🏷 Janr: {a.genre}'
    if a.year:
        text += f'\n📅 Yil: {a.year}'
    if a.description:
        text += f'\n\n{a.description}'
    await c.message.edit_text(text, reply_markup=anime_actions(aid, not favorite))
    await c.answer()


@router.callback_query(F.data.startswith('episodes:'))
async def episodes(c: CallbackQuery, db, settings):
    try:
        _, aid, p = c.data.split(':')
        aid, p = int(aid), max(0, int(p))
    except (ValueError, IndexError):
        return await c.answer('❌ Qism sahifasi xatosi.', show_alert=True)
    a = await db.anime.get(aid)
    if not a or a.status == 'deleted':
        return await c.answer('Anime topilmadi.', show_alert=True)
    es = await db.episodes.list(aid, p * settings.pagination_size, settings.pagination_size)
    await c.message.edit_text('📺 <b>Qismlar</b>\n\nKerakli qismni tanlang:', reply_markup=episodes_page(aid, es, p, settings.pagination_size))
    await c.answer()


@router.callback_query(F.data.startswith('ep_page:'))
async def ep_page(c: CallbackQuery, db, settings):
    try:
        _, aid, p = c.data.split(':')
        aid, p = int(aid), max(0, int(p))
    except (ValueError, IndexError):
        return await c.answer('❌ Sahifa xatosi.', show_alert=True)
    es = await db.episodes.list(aid, p * settings.pagination_size, settings.pagination_size)
    await c.message.edit_reply_markup(reply_markup=episodes_page(aid, es, p, settings.pagination_size))
    await c.answer()


@router.callback_query(F.data.startswith('episode:'))
async def episode(c: CallbackQuery, db, settings):
    try:
        _, aid, num = c.data.split(':')
        aid, num = int(aid), int(num)
    except (ValueError, IndexError):
        return await c.answer('❌ Qism ID xatosi.', show_alert=True)
    e = await db.episodes.get(aid, num)
    a = await db.anime.get(aid)
    if not e or not a or a.status == 'deleted':
        return await c.answer('Qism topilmadi.', show_alert=True)
    e.views += 1
    await db.s.commit()
    u = await db.user.upsert(c.from_user.id, c.from_user.username, c.from_user.first_name, is_admin(c.from_user.id, settings))
    await db.progress.set(u.id, aid, num)
    prev = await db.episodes.get(aid, num - 1)
    nxt = await db.episodes.get(aid, num + 1)
    await c.message.answer_video(e.telegram_file_id, caption=f'🎬 {a.title}\n📺 {num}-qism', reply_markup=episode_nav(aid, prev.episode_number if prev else None, nxt.episode_number if nxt else None))
    await c.answer()


@router.callback_query(F.data.startswith('fav:'))
async def favorite(c: CallbackQuery, db, settings):
    try:
        aid = int(c.data.split(':', 1)[1])
    except (ValueError, IndexError):
        return await c.answer('❌ Anime ID xatosi.', show_alert=True)
    a = await db.anime.get(aid)
    if not a or a.status == 'deleted':
        return await c.answer('Anime topilmadi.', show_alert=True)
    u = await db.user.upsert(c.from_user.id, c.from_user.username, c.from_user.first_name, is_admin(c.from_user.id, settings))
    added = await db.fav.toggle(u.id, aid)
    await c.answer('⭐ Sevimlilarga qo‘shildi.' if added else '☆ Sevimlilardan chiqarildi.')


@router.message(F.text == '⭐ Sevimlilar')
async def favorites_button(m: Message, db, settings):
    await favorites_show(m, db, settings)


@router.callback_query(F.data == 'favorites')
async def favorites(c: CallbackQuery, db, settings):
    await favorites_show(c.message, db, settings, True)
    await c.answer()


async def favorites_show(m, db, settings, edit=False):
    u = await db.user.upsert(m.from_user.id, m.from_user.username, m.from_user.first_name, is_admin(m.from_user.id, settings))
    items = await db.fav.list(u.id)
    text = '⭐ <b>Sevimlilar</b>\n\n' + ('Ro‘yxat bo‘sh.' if not items else '\n'.join(f'🎬 {a.title}' for a in items))
    markup = ikb([[(a.title, f'anime:{a.id}')] for a in items] + [[('🏠 Bosh menyu', 'home')]])
    if edit:
        await m.edit_text(text, reply_markup=markup)
    else:
        await m.answer(text, reply_markup=markup)


@router.message(F.text == '🆕 Yangiliklar')
async def latest_button(m: Message, db, settings):
    await latest_show(m, db, settings)


@router.callback_query(F.data == 'latest')
async def latest(c: CallbackQuery, db, settings):
    await latest_show(c.message, db, settings, True)
    await c.answer()


async def latest_show(m, db, settings, edit=False):
    items = await db.anime.list(0, settings.pagination_size)
    text = '🆕 <b>So‘nggi qo‘shilganlar</b>\n\n' + ('Hozircha yo‘q.' if not items else '\n'.join(f'🎬 {a.title}' for a in items))
    markup = ikb([[(a.title, f'anime:{a.id}')] for a in items] + [[('🏠 Bosh menyu', 'home')]])
    if edit:
        await m.edit_text(text, reply_markup=markup)
    else:
        await m.answer(text, reply_markup=markup)


@router.message(F.text == '🔎 Qidirish')
async def search_button(m: Message, state: FSMContext):
    await state.set_state(Search.query)
    await m.answer('🔎 Anime nomi, muqobil nomi yoki janrini yozing:')


@router.callback_query(F.data == 'search')
async def search_start(c: CallbackQuery, state: FSMContext):
    await state.set_state(Search.query)
    await c.message.edit_text('🔎 Anime nomi, muqobil nomi yoki janrini yuboring:')
    await c.answer()


@router.message(Search.query)
async def search(m: Message, state: FSMContext, db, settings):
    q = (m.text or '').strip()
    if not q:
        return await m.answer('❌ Qidiruv matnini kiriting.')
    items = await db.anime.search(q)
    await state.clear()
    text = '🔎 <b>Natijalar</b>\n\n' + ('Hech narsa topilmadi.' if not items else '\n'.join(f'🎬 {a.title}' for a in items))
    await m.answer(text, reply_markup=ikb([[(a.title, f'anime:{a.id}')] for a in items] + [[('🏠 Bosh menyu', 'home')]]))


@router.message(F.text == '📺 Davom ettirish')
async def continue_watch(m: Message, db, settings):
    u = await db.user.upsert(m.from_user.id, m.from_user.username, m.from_user.first_name, is_admin(m.from_user.id, settings))
    rows = (await db.session.execute(select(WatchProgress, Anime).join(Anime, Anime.id == WatchProgress.anime_id).where(WatchProgress.user_id == u.id, Anime.status != 'deleted').order_by(WatchProgress.updated_at.desc()))).all()
    if not rows:
        return await m.answer('📺 Hali davom ettiriladigan anime yo‘q.')
    await m.answer('📺 <b>Davom ettirish</b>\n\n' + '\n'.join(f'🎬 {a.title} — {p.episode_number}-qism' for p, a in rows), reply_markup=ikb([[(f'▶️ {a.title}', f'episode:{a.id}:{p.episode_number}')] for p, a in rows] + [[('🏠 Bosh menyu', 'home')]]))


@router.message(F.text == '👤 Profil')
async def profile(m: Message, db, settings):
    u = await db.user.upsert(m.from_user.id, m.from_user.username, m.from_user.first_name, is_admin(m.from_user.id, settings))
    favs = len(await db.fav.list(u.id))
    views = (await db.session.execute(select(func.coalesce(func.sum(Episode.views), 0)))).scalar_one()
    await m.answer(f'👤 <b>Profil</b>\n\n🆔 ID: <code>{u.telegram_id}</code>\n⭐ Sevimlilar: {favs}\n🌐 Holat: faol\n👁 Botdagi jami ko‘rishlar: {views}')


@router.callback_query(F.data == 'home')
async def home(c: CallbackQuery, settings):
    await c.message.edit_text(home_text(), reply_markup=inline_home(is_admin(c.from_user.id, settings)))
    await c.answer()


@router.callback_query(F.data == 'help')
async def help_callback(c: CallbackQuery, settings):
    await c.message.edit_text('ℹ️ <b>AniEasy yordam</b>\n\nPastdagi menyu orqali anime qidiring, sevimliga saqlang va davom ettiring.', reply_markup=inline_home(is_admin(c.from_user.id, settings)))
    await c.answer()
