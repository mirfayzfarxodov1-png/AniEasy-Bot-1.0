from aiogram import Router,F
from aiogram.filters import Command
from aiogram.types import Message,CallbackQuery
from .keyboards import admin_menu,kb
from .states import EditAnime

router=Router()

def ok(uid,s): return uid in s.admin_ids

@router.message(Command('anime'))
async def anime_cmd(m:Message,db,settings):
    items=await db.anime.list(0,settings.pagination_size)
    await m.answer('📭 Hozircha anime mavjud emas.' if not items else '🎬 Anime:\n\n'+'\n'.join(f'🎬 {a.title}' for a in items),reply_markup=kb([[(a.title,f'anime:{a.id}')] for a in items]+[[('🏠 Bosh menyu','home')]]))

@router.message(Command('search'))
async def search_cmd(m:Message): await m.answer('🔎 Qidiruv uchun menyudagi “Qidirish” tugmasidan foydalaning.')

@router.message(Command('favorites'))
async def favorites_cmd(m:Message): await m.answer('⭐ Sevimlilar bo‘limini /start orqali oching.')

@router.callback_query(F.data=='admin_animes')
async def admin_animes(c:CallbackQuery,db,settings):
    if not ok(c.from_user.id,settings): return await c.answer('❌ Ruxsat yo‘q.',show_alert=True)
    items=await db.anime.list(0,settings.pagination_size)
    rows=[[(f'🎬 {a.title}',f'anime:{a.id}')] for a in items]
    rows.append([('⬅️ Orqaga','admin')]); await c.message.edit_text('📚 Anime ro‘yxati',reply_markup=kb(rows)); await c.answer()

@router.callback_query(F.data.startswith('del_anime:'))
async def del_anime(c:CallbackQuery,db,settings):
    if not ok(c.from_user.id,settings): return await c.answer('❌ Ruxsat yo‘q.',show_alert=True)
    aid=int(c.data.split(':')[1]); a=await db.anime.get(aid)
    if not a: return await c.answer('Anime topilmadi.',show_alert=True)
    await c.message.edit_text(f'⚠️ Rostdan ham “{a.title}”ni o‘chirmoqchimisiz?',reply_markup=kb([[('❌ Bekor qilish','admin_animes'),('🗑 Ha, o‘chirish',f'del_confirm:{aid}')]])); await c.answer()

@router.callback_query(F.data.startswith('del_confirm:'))
async def del_confirm(c:CallbackQuery,db,settings):
    if not ok(c.from_user.id,settings): return await c.answer('❌ Ruxsat yo‘q.',show_alert=True)
    a=await db.anime.get(int(c.data.split(':')[1]));
    if a: await db.anime.delete(a)
    await c.message.edit_text('🗑 Anime o‘chirildi.',reply_markup=admin_menu()); await c.answer()
