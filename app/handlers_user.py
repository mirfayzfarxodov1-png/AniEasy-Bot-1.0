from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from .keyboards import main_menu, kb, episodes_page, episode_nav
from .states import Search
from .repositories import AnimeRepository, EpisodeRepository, FavoriteRepository

router=Router()

def txt(a): return f'🎬 {a.title}\n📺 Qismlar soni: {getattr(a,"episode_count",0)}'

@router.message(Command('start'))
async def start(m:Message, db, settings):
    is_admin=m.from_user.id in settings.admin_ids
    await db.user.upsert(m.from_user.id,m.from_user.username,m.from_user.first_name,is_admin)
    await m.answer('🏠 Bosh menyu\n\nKerakli bo‘limni tanlang:',reply_markup=main_menu(is_admin))

@router.message(Command('help'))
async def help_cmd(m:Message): await m.answer('ℹ️ Yordam\n\nAnime tanlang, qismni bosing va videoni ko‘ring. Qidirish uchun 🔎 Qidirish bo‘limidan foydalaning.')

@router.callback_query(F.data=='anime')
async def anime_list(c:CallbackQuery, db, settings):
    items=await db.anime.list(0,settings.pagination_size)
    if not items: return await c.message.edit_text('📭 Hozircha anime mavjud emas.',reply_markup=main_menu(c.from_user.id in settings.admin_ids))
    await c.message.edit_text('🎬 Anime\n\n'+ '\n'.join(f'🎬 {a.title}' for a in items),reply_markup=kb([[(a.title,f'anime:{a.id}')] for a in items]+[[('🏠 Bosh menyu','home')]])); await c.answer()

@router.callback_query(F.data.startswith('anime:'))
async def anime_detail(c:CallbackQuery,db):
    aid=int(c.data.split(':')[1]); a=await db.anime.get(aid); n=await db.episodes.count(aid)
    if not a: return await c.answer('Anime topilmadi.',show_alert=True)
    await c.message.edit_text(f'🎬 {a.title}\n📺 Qismlar soni: {n}\n'+(f'\n{a.description}' if a.description else ''),reply_markup=kb([[('📺 Qismlar',f'episodes:{aid}:0'),('⭐ Sevimli',f'fav:{aid}')],[('⬅️ Orqaga','anime'),('🏠 Bosh menyu','home')]])); await c.answer()

@router.callback_query(F.data.startswith('episodes:'))
async def episodes(c:CallbackQuery,db,settings):
    _,aid,p=c.data.split(':'); aid=int(aid); p=int(p); es=await db.episodes.list(aid,p*settings.pagination_size,settings.pagination_size)
    await c.message.edit_text('📺 Qismlar:',reply_markup=episodes_page(aid,es,p,settings.pagination_size)); await c.answer()

@router.callback_query(F.data.startswith('ep_page:'))
async def ep_page(c:CallbackQuery,db,settings):
    _,aid,p=c.data.split(':'); aid=int(aid); p=int(p); es=await db.episodes.list(aid,p*settings.pagination_size,settings.pagination_size); await c.message.edit_reply_markup(reply_markup=episodes_page(aid,es,p,settings.pagination_size)); await c.answer()

@router.callback_query(F.data.startswith('episode:'))
async def episode(c:CallbackQuery,db):
    _,aid,num=c.data.split(':'); aid=int(aid); num=int(num); e=await db.episodes.get(aid,num); a=await db.anime.get(aid)
    if not e or not a: return await c.answer('Qism topilmadi.',show_alert=True)
    e.views+=1; await db.s.commit(); prev=await db.episodes.get(aid,num-1); nxt=await db.episodes.get(aid,num+1)
    await c.message.answer_video(e.telegram_file_id,caption=f'🎬 {a.title}\n📺 {num}-qism',reply_markup=episode_nav(aid,prev.episode_number if prev else None,nxt.episode_number if nxt else None)); await c.answer()

@router.callback_query(F.data.startswith('fav:'))
async def favorite(c:CallbackQuery,db):
    aid=int(c.data.split(':')[1]); u=await db.user.upsert(c.from_user.id,c.from_user.username,c.from_user.first_name); added=await db.fav.toggle(u.id,aid); await c.answer('⭐ Sevimlilarga qo‘shildi.' if added else '☆ Sevimlilardan chiqarildi.')

@router.callback_query(F.data=='favorites')
async def favorites(c:CallbackQuery,db):
    u=await db.user.upsert(c.from_user.id,c.from_user.username,c.from_user.first_name); items=await db.fav.list(u.id); await c.message.edit_text('⭐ Sevimlilar ro‘yxati bo‘sh.' if not items else '⭐ Sevimlilar:\n\n'+'\n'.join(f'🎬 {a.title}' for a in items),reply_markup=main_menu(c.from_user.id in c.bot.settings.admin_ids if hasattr(c.bot,'settings') else False)); await c.answer()

@router.callback_query(F.data=='search')
async def search_start(c:CallbackQuery,state:FSMContext): await state.set_state(Search.query); await c.message.edit_text('🔎 Anime nomini yuboring:'); await c.answer()

@router.message(Search.query)
async def search(m:Message,state:FSMContext,db):
    items=await db.anime.search(m.text or ''); await state.clear(); await m.answer('🔎 Hech narsa topilmadi.' if not items else '🔎 Natijalar:\n\n'+'\n'.join(f'🎬 {a.title}' for a in items),reply_markup=kb([[(a.title,f'anime:{a.id}')] for a in items]+[[('🏠 Bosh menyu','home')]]))

@router.callback_query(F.data=='home')
async def home(c:CallbackQuery,settings): await c.message.edit_text('🏠 Bosh menyu\n\nKerakli bo‘limni tanlang:',reply_markup=main_menu(c.from_user.id in settings.admin_ids)); await c.answer()
