import re
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from .states import AddAnime, Upload
from .keyboards import admin_menu, kb
from .services import parse_episode

router=Router()

def admin_only(uid,settings): return uid in settings.admin_ids

@router.message(Command('admin'))
async def admin_cmd(m:Message,settings):
    if not admin_only(m.from_user.id,settings): return await m.answer('❌ Sizda admin huquqi mavjud emas.')
    await m.answer('👑 ADMIN PANEL',reply_markup=admin_menu())

@router.callback_query(F.data=='admin')
async def admin(c:CallbackQuery,settings):
    if not admin_only(c.from_user.id,settings): return await c.answer('❌ Ruxsat yo‘q.',show_alert=True)
    await c.message.edit_text('👑 ADMIN PANEL',reply_markup=admin_menu()); await c.answer()

@router.callback_query(F.data=='admin_add')
async def add_start(c:CallbackQuery,state:FSMContext,settings):
    if not admin_only(c.from_user.id,settings): return await c.answer('❌ Ruxsat yo‘q.',show_alert=True)
    await state.set_state(AddAnime.title); await c.message.edit_text('🎬 Yangi anime qo‘shish\n\nAnime nomini yuboring:'); await c.answer()

@router.message(AddAnime.title)
async def add_title(m:Message,state:FSMContext,db,settings):
    if not admin_only(m.from_user.id,settings): return
    title=(m.text or '').strip()
    if not title: return await m.answer('❌ Anime nomi bo‘sh bo‘lishi mumkin emas.')
    a=await db.anime.create(title=title); await state.set_state(Upload.episodes); await state.update_data(anime_id=a.id,next_episode=1)
    await m.answer(f'✅ Anime yaratildi: {a.title}\n\nEndi qismlarni ketma-ket yuboring.\n1-qismdan boshlang.\n\nYakunlash uchun tugmani bosing.',reply_markup=kb([[('⏭ Yakunlash','upload_finish')],[('❌ Bekor qilish','upload_cancel')]]))

@router.message(Upload.episodes, F.video)
async def upload_video(m:Message,state:FSMContext,db,settings):
    if not admin_only(m.from_user.id,settings): return
    data=await state.get_data(); aid=data['anime_id']; expected=int(data.get('next_episode',1)); detected=parse_episode(m.caption)
    number=detected or expected
    old=await db.episodes.get(aid,number)
    if old:
        await state.update_data(pending_file_id=m.video.file_id,pending_unique_id=m.video.file_unique_id,pending_caption=m.caption or '',pending_number=number)
        return await m.answer(f'⚠️ Bu qism allaqachon mavjud.\n\n📺 {number}-qism\n\n[Yangilash] yoki [Bekor qilish] tugmalaridan foydalaning.',reply_markup=kb([[('🔄 Yangilash',f'replace:{number}'),('❌ Bekor qilish','replace_cancel')]]))
    await db.episodes.add(anime_id=aid,episode_number=number,telegram_file_id=m.video.file_id,file_unique_id=m.video.file_unique_id,caption=m.caption)
    await state.update_data(next_episode=max(expected,number+1))
    await m.answer(f'✅ {number}-qism qabul qilindi.\n\nKeyingi: {number+1}-qism',reply_markup=kb([[('⏭ Yakunlash','upload_finish')],[('❌ Bekor qilish','upload_cancel')]]))

@router.message(Upload.episodes)
async def upload_wrong(m:Message): await m.answer('📺 Iltimos, qism videosini yuboring yoki “Yakunlash” tugmasini bosing.')

@router.callback_query(F.data=='upload_finish')
async def finish(c:CallbackQuery,state:FSMContext,db,settings):
    if not admin_only(c.from_user.id,settings): return await c.answer('❌ Ruxsat yo‘q.',show_alert=True)
    data=await state.get_data(); aid=data['anime_id']; a=await db.anime.get(aid); count=await db.episodes.count(aid); missing=await db.episodes.missing(aid)
    if missing: return await c.answer('⚠️ Yetishmayotgan qismlar: '+', '.join(map(str,missing)),show_alert=True)
    await state.clear(); await c.message.edit_text(f'🎉 Yuklash yakunlandi!\n\n🎬 {a.title}\n📺 Jami: {count} qism',reply_markup=kb([[('📚 Qismlar',f'episodes:{aid}:0')],[('✏️ Tahrirlash',f'edit_anime:{aid}')],[('👑 Admin panel','admin')]])); await c.answer()

@router.callback_query(F.data=='upload_cancel')
async def cancel(c:CallbackQuery,state:FSMContext): await state.clear(); await c.message.edit_text('❌ Yuklash bekor qilindi.',reply_markup=admin_menu()); await c.answer()

@router.callback_query(F.data.startswith('replace:'))
async def replace(c:CallbackQuery,state:FSMContext,db):
    num=int(c.data.split(':')[1]); d=await state.get_data(); old=await db.episodes.get(d['anime_id'],num)
    await db.episodes.replace(old,telegram_file_id=d['pending_file_id'],file_unique_id=d['pending_unique_id'],caption=d['pending_caption']); await state.update_data(next_episode=num+1); await c.message.edit_text(f'✅ {num}-qism yangilandi.\n\nKeyingi: {num+1}-qism',reply_markup=kb([[('⏭ Yakunlash','upload_finish')]])); await c.answer()

@router.callback_query(F.data=='replace_cancel')
async def replace_cancel(c:CallbackQuery,state:FSMContext): await state.update_data(pending_file_id=None,pending_unique_id=None,pending_caption=None,pending_number=None); await c.message.edit_text('❌ Yangilash bekor qilindi. Videoni davom ettirishingiz mumkin.'); await c.answer()

@router.callback_query(F.data=='admin_stats')
async def stats(c:CallbackQuery,db,settings):
    if not admin_only(c.from_user.id,settings): return await c.answer('❌ Ruxsat yo‘q.',show_alert=True)
    ac=await db.anime.count(); from sqlalchemy import func,select; from .models import Episode,User
    ec=(await db.session.execute(select(func.count()).select_from(Episode))).scalar_one(); uc=(await db.session.execute(select(func.count()).select_from(User))).scalar_one(); views=(await db.session.execute(select(func.coalesce(func.sum(Episode.views),0)))).scalar_one()
    await c.message.edit_text(f'📊 Statistika\n\n👥 Foydalanuvchilar: {uc}\n🎬 Anime: {ac}\n📺 Qismlar: {ec}\n👁 Ko‘rishlar: {views}',reply_markup=admin_menu()); await c.answer()
