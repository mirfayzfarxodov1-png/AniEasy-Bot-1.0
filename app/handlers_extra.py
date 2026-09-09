from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from .keyboards import admin_menu, ikb, inline_home
from .states import EditAnime
from .models import Anime

router=Router()

def ok(uid,s): return uid in s.admin_ids

@router.callback_query(F.data=='genres')
async def genres_callback(c:CallbackQuery,db,settings):
    vals=(await db.session.execute(select(Anime.genre).where(Anime.genre.is_not(None),Anime.status!='deleted'))).scalars().all(); genres=sorted({part.strip() for value in vals for part in value.split(',') if part.strip()}); text='🎭 <b>Janrlar</b>\n\n'+('\n'.join(f'• {g}' for g in genres) if genres else 'Janrlar hali kiritilmagan.')
    await c.message.edit_text(text,reply_markup=inline_home(ok(c.from_user.id,settings))); await c.answer()

@router.callback_query(F.data=='profile')
async def profile_callback(c:CallbackQuery,db,settings):
    u=await db.user.upsert(c.from_user.id,c.from_user.username,c.from_user.first_name,ok(c.from_user.id,settings)); favs=len(await db.fav.list(u.id)); await c.message.edit_text(f'👤 <b>Profil</b>\n\n🆔 <code>{u.telegram_id}</code>\n👤 {u.first_name or "Noma’lum"}\n⭐ Sevimlilar: {favs}\n🟢 Holat: faol',reply_markup=inline_home(ok(c.from_user.id,settings))); await c.answer()

@router.callback_query(F.data=='continue')
async def continue_callback(c:CallbackQuery,db,settings):
    from .models import WatchProgress
    u=await db.user.upsert(c.from_user.id,c.from_user.username,c.from_user.first_name,ok(c.from_user.id,settings)); rows=(await db.session.execute(select(WatchProgress,Anime).join(Anime,Anime.id==WatchProgress.anime_id).where(WatchProgress.user_id==u.id).order_by(WatchProgress.updated_at.desc()))).all()
    if not rows: return await c.answer('Hali davom ettiriladigan anime yo‘q.',show_alert=True)
    await c.message.edit_text('📺 <b>Davom ettirish</b>\n\n'+ '\n'.join(f'🎬 {a.title} — {p.episode_number}-qism' for p,a in rows),reply_markup=ikb([[(f'▶️ {a.title}',f'episode:{a.id}:{p.episode_number}')] for p,a in rows]+[[('🏠 Bosh menyu','home')]])); await c.answer()

@router.callback_query(F.data.startswith('edit_anime:'))
async def edit_anime(c:CallbackQuery,state:FSMContext,db,settings):
    if not ok(c.from_user.id,settings): return await c.answer('❌ Ruxsat yo‘q.',show_alert=True)
    aid=int(c.data.split(':')[1]); a=await db.anime.get(aid)
    if not a: return await c.answer('Anime topilmadi.',show_alert=True)
    await state.set_state(EditAnime.field); await state.update_data(anime_id=aid); await c.message.edit_text(f'✏️ <b>{a.title}</b>\n\nNimani tahrirlaysiz?',reply_markup=ikb([[('🏷 Nomi','edit_field:title'),('📝 Tavsif','edit_field:description')],[('🎭 Janr','edit_field:genre'),('📅 Yil','edit_field:year')],[('🔤 Muqobil nom','edit_field:alternate_title')],[('⬅️ Orqaga',f'anime:{aid}')]])); await c.answer()

@router.callback_query(F.data.startswith('edit_field:'))
async def edit_field(c:CallbackQuery,state:FSMContext):
    field=c.data.split(':',1)[1]; await state.update_data(field=field); await state.set_state(EditAnime.value); await c.message.edit_text(f'✏️ <b>{field}</b> uchun yangi qiymatni yuboring:'); await c.answer()

@router.message(EditAnime.value)
async def edit_value(m:Message,state:FSMContext,db,settings):
    if not ok(m.from_user.id,settings): return
    d=await state.get_data(); a=await db.anime.get(d.get('anime_id')); field=d.get('field'); value=(m.text or '').strip()
    if not a or field not in {'title','description','genre','year','alternate_title'}: await state.clear(); return await m.answer('❌ Tahrirlash ma’lumotlari topilmadi.')
    if field=='year':
        try: value=int(value)
        except ValueError: return await m.answer('📅 Yil faqat raqam bo‘lishi kerak.')
    setattr(a,field,value); await db.anime.save(a); await state.clear(); await m.answer(f'✅ {field} yangilandi: {value}',reply_markup=admin_menu())

@router.callback_query(F.data.startswith('del_anime:'))
async def del_anime(c:CallbackQuery,db,settings):
    if not ok(c.from_user.id,settings): return await c.answer('❌ Ruxsat yo‘q.',show_alert=True)
    aid=int(c.data.split(':')[1]); a=await db.anime.get(aid)
    if not a: return await c.answer('Anime topilmadi.',show_alert=True)
    await c.message.edit_text(f'⚠️ Rostdan ham “{a.title}”ni o‘chirmoqchimisiz?',reply_markup=ikb([[('❌ Bekor','anime:'+str(aid)),('🗑 Ha, o‘chirish',f'del_confirm:{aid}')]])); await c.answer()

@router.callback_query(F.data.startswith('del_confirm:'))
async def del_confirm(c:CallbackQuery,db,settings):
    if not ok(c.from_user.id,settings): return await c.answer('❌ Ruxsat yo‘q.',show_alert=True)
    a=await db.anime.get(int(c.data.split(':')[1]));
    if a: await db.anime.delete(a)
    await c.message.edit_text('🗑 Anime o‘chirildi.'); await c.message.answer('👑 Admin menyu:',reply_markup=admin_menu()); await c.answer()

@router.callback_query(F.data=='admin_animes')
async def admin_animes_callback(c:CallbackQuery,db,settings):
    if not ok(c.from_user.id,settings): return await c.answer('❌ Ruxsat yo‘q.',show_alert=True)
    items=await db.anime.list(0,settings.pagination_size); await c.message.edit_text('📚 <b>Anime boshqaruvi</b>\n\n'+('Ro‘yxat bo‘sh.' if not items else '\n'.join(f'🎬 {a.title}' for a in items)),reply_markup=ikb([[(a.title,f'anime:{a.id}')] for a in items]+[[('🏠 Admin','admin')]])); await c.answer()
