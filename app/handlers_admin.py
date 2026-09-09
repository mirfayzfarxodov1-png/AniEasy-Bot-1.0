import re
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import func, select
from .states import AddAnime, Upload, Broadcast, EditAnime
from .keyboards import admin_menu, ikb
from .services import parse_episode
from .models import Episode, User, Anime

router=Router()

def admin_only(uid,settings): return uid in settings.admin_ids

def deny(m): return m.answer('❌ Bu bo‘lim faqat adminlar uchun.')

def panel_text(): return '👑 <b>AniEasy Admin Panel</b>\n\nKerakli boshqaruv bo‘limini tanlang:'

@router.message(Command('admin'))
@router.message(F.text=='👑 Admin panel')
async def admin_cmd(m:Message,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    await m.answer(panel_text(),reply_markup=admin_menu())

@router.callback_query(F.data=='admin')
async def admin_callback(c:CallbackQuery,settings):
    if not admin_only(c.from_user.id,settings): return await c.answer('❌ Ruxsat yo‘q.',show_alert=True)
    await c.message.edit_text(panel_text()); await c.message.answer('👑 Admin menyu:',reply_markup=admin_menu()); await c.answer()

@router.message(F.text=='➕ Anime qo‘shish')
@router.callback_query(F.data=='admin_add')
async def add_start(x,state:FSMContext,settings):
    uid=x.from_user.id
    if not admin_only(uid,settings): return await (x.answer('❌ Ruxsat yo‘q.',show_alert=True) if isinstance(x,CallbackQuery) else deny(x))
    await state.set_state(AddAnime.title); msg=x.message if isinstance(x,CallbackQuery) else x
    await msg.answer('➕ <b>Anime qo‘shish</b>\n\nAnime nomini yuboring:') if isinstance(x,CallbackQuery) else await msg.answer('➕ <b>Anime qo‘shish</b>\n\nAnime nomini yuboring:')
    if isinstance(x,CallbackQuery): await x.answer()

@router.message(AddAnime.title)
async def add_title(m:Message,state:FSMContext,db,settings):
    if not admin_only(m.from_user.id,settings): return
    title=(m.text or '').strip()
    if not title: return await m.answer('❌ Anime nomi bo‘sh bo‘lishi mumkin emas.')
    old=await db.anime.search(title,1)
    if old and old[0].title.lower()==title.lower(): return await m.answer('⚠️ Bu anime allaqachon mavjud. Boshqa nom kiriting.')
    a=await db.anime.create(title=title); await state.set_state(Upload.episodes); await state.update_data(anime_id=a.id,next_episode=1)
    await m.answer(f'✅ <b>{a.title}</b> yaratildi.\n\n🎞 Videolarni ketma-ket yuboring. Caption ichidagi <code>7-qism</code> kabi raqam avtomatik aniqlanadi.',reply_markup=ikb([[('⏭ Yakunlash','upload_finish'),('❌ Bekor qilish','upload_cancel')]]))

@router.message(Upload.episodes,F.video)
async def upload_video(m:Message,state:FSMContext,db,settings):
    if not admin_only(m.from_user.id,settings): return
    d=await state.get_data(); aid=d['anime_id']; expected=int(d.get('next_episode',1)); number=parse_episode(m.caption) or expected
    old=await db.episodes.get(aid,number)
    if old:
        await state.update_data(pending_file_id=m.video.file_id,pending_unique_id=m.video.file_unique_id,pending_caption=m.caption or '',pending_number=number)
        return await m.answer(f'⚠️ {number}-qism mavjud. Yangilaysizmi?',reply_markup=ikb([[('🔄 Yangilash',f'replace:{number}'),('❌ Bekor qilish','replace_cancel')]]))
    await db.episodes.add(anime_id=aid,episode_number=number,telegram_file_id=m.video.file_id,file_unique_id=m.video.file_unique_id,caption=m.caption)
    await state.update_data(next_episode=max(expected,number+1)); await m.answer(f'✅ {number}-qism saqlandi. Keyingi: {number+1}-qism',reply_markup=ikb([[('⏭ Yakunlash','upload_finish'),('❌ Bekor qilish','upload_cancel')]]))

@router.message(Upload.episodes)
async def upload_wrong(m:Message): await m.answer('📺 Video yuboring yoki Yakunlash tugmasini bosing.')

@router.callback_query(F.data=='upload_finish')
async def finish(c:CallbackQuery,state:FSMContext,db,settings):
    if not admin_only(c.from_user.id,settings): return await c.answer('❌ Ruxsat yo‘q.',show_alert=True)
    d=await state.get_data(); aid=d.get('anime_id'); a=await db.anime.get(aid); count=await db.episodes.count(aid); missing=await db.episodes.missing(aid)
    if missing: return await c.answer('⚠️ Yetishmayotgan: '+', '.join(map(str,missing)),show_alert=True)
    await state.clear(); await c.message.edit_text(f'🎉 <b>{a.title}</b> yuklash yakunlandi!\n📺 {count} qism'); await c.message.answer('👑 Admin menyu:',reply_markup=admin_menu()); await c.answer()

@router.callback_query(F.data=='upload_cancel')
async def cancel(c:CallbackQuery,state:FSMContext): await state.clear(); await c.message.edit_text('❌ Yuklash bekor qilindi.'); await c.message.answer('👑 Admin menyu:',reply_markup=admin_menu()); await c.answer()

@router.callback_query(F.data.startswith('replace:'))
async def replace(c:CallbackQuery,state:FSMContext,db):
    d=await state.get_data(); old=await db.episodes.get(d.get('anime_id'),int(c.data.split(':')[1]))
    if not old: return await c.answer('Qism topilmadi.',show_alert=True)
    await db.episodes.replace(old,telegram_file_id=d['pending_file_id'],file_unique_id=d['pending_unique_id'],caption=d['pending_caption']); n=int(c.data.split(':')[1]); await state.update_data(next_episode=n+1); await c.message.edit_text(f'✅ {n}-qism yangilandi. Keyingi: {n+1}-qism'); await c.answer()

@router.callback_query(F.data=='replace_cancel')
async def replace_cancel(c:CallbackQuery,state:FSMContext): await state.update_data(pending_file_id=None,pending_unique_id=None,pending_caption=None,pending_number=None); await c.message.edit_text('❌ Yangilash bekor qilindi.'); await c.answer()

@router.message(F.text=='📚 Anime boshqarish')
@router.callback_query(F.data=='admin_animes')
async def admin_animes(x,db,settings):
    if not admin_only(x.from_user.id,settings): return await (x.answer('❌ Ruxsat yo‘q.',show_alert=True) if isinstance(x,CallbackQuery) else deny(x))
    items=await db.anime.list(0,settings.pagination_size); text='📚 <b>Anime boshqaruvi</b>\n\n'+('Ro‘yxat bo‘sh.' if not items else '\n'.join(f'• {a.title} — {await db.episodes.count(a.id)} qism' for a in items)); markup=ikb([[(f'🎬 {a.title}',f'anime:{a.id}')] for a in items]+[[('🏠 Admin','admin')]]); msg=x.message if isinstance(x,CallbackQuery) else x; await msg.answer(text,reply_markup=markup) if isinstance(x,Message) else await msg.edit_text(text,reply_markup=markup)
    if isinstance(x,CallbackQuery): await x.answer()

@router.message(F.text=='📺 Qismlar')
async def episode_manager(m:Message,db,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    items=await db.anime.list(0,settings.pagination_size); await m.answer('📺 <b>Qaysi anime qismlarini boshqaramiz?</b>',reply_markup=ikb([[(a.title,f'episodes:{a.id}:0')] for a in items]+[[('👑 Admin','admin')]]))

@router.message(F.text=='📊 Statistika')
@router.callback_query(F.data=='admin_stats')
async def stats(x,db,settings):
    if not admin_only(x.from_user.id,settings): return await (x.answer('❌ Ruxsat yo‘q.',show_alert=True) if isinstance(x,CallbackQuery) else deny(x))
    ac=await db.anime.count(); ec=(await db.session.execute(select(func.count()).select_from(Episode))).scalar_one(); uc=(await db.session.execute(select(func.count()).select_from(User))).scalar_one(); views=(await db.session.execute(select(func.coalesce(func.sum(Episode.views),0)))).scalar_one(); active=(await db.session.execute(select(func.count()).select_from(User).where(User.last_active.is_not(None)))).scalar_one()
    text=f'📊 <b>Bot statistikasi</b>\n\n👥 Foydalanuvchilar: {uc}\n🟢 Faol profillar: {active}\n🎬 Anime: {ac}\n📺 Qismlar: {ec}\n👁 Ko‘rishlar: {views}'
    if isinstance(x,CallbackQuery): await x.message.edit_text(text); await x.answer()
    else: await x.answer(text,reply_markup=admin_menu())

@router.message(F.text=='👥 Foydalanuvchilar')
async def users(m:Message,db,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    rows=(await db.session.execute(select(User).order_by(User.last_active.desc()).limit(15))).scalars().all(); text='👥 <b>Oxirgi foydalanuvchilar</b>\n\n'+('\n'.join(f'• {u.first_name or "Noma’lum"} — <code>{u.telegram_id}</code>' for u in rows) if rows else 'Foydalanuvchi yo‘q.'); await m.answer(text,reply_markup=admin_menu())

@router.message(F.text=='⚙️ Sozlamalar')
async def settings(m:Message,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    await m.answer(f'⚙️ <b>Sozlamalar</b>\n\n📄 Shablon: <code>{settings.description_template}</code>\n📄 Sahifadagi limit: {settings.pagination_size}\n📢 Kanal: {settings.channel_id or "o‘rnatilmagan"}\n🌐 WebApp: {"yoqilgan" if settings.webapp_url else "URL kiritilmagan"}',reply_markup=admin_menu())

@router.message(F.text=='💾 Backup')
async def backup(m:Message,db,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    ac=await db.anime.count(); ec=(await db.session.execute(select(func.count()).select_from(Episode))).scalar_one(); uc=(await db.session.execute(select(func.count()).select_from(User))).scalar_one(); await m.answer(f'💾 <b>Backup nazorati</b>\n\nDB turi: {settings.database_url.split(":",1)[0]}\nAnime: {ac}\nQismlar: {ec}\nFoydalanuvchilar: {uc}\n\n⚠️ To‘liq fayl backup server/VPS darajasida amalga oshiriladi.',reply_markup=admin_menu())

@router.message(F.text=='📣 Kanal')
async def channel(m:Message,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    await m.answer(f'📣 <b>Kanal</b>\n\nCHANNEL_ID: {settings.channel_id or "o‘rnatilmagan"}\nLOG_CHANNEL_ID: {settings.log_channel_id or "o‘rnatilmagan"}',reply_markup=admin_menu())

@router.message(F.text=='🛡 Adminlar')
async def admins(m:Message,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    await m.answer('🛡 <b>Adminlar</b>\n\nAdmin IDlar: '+', '.join(map(str,settings.admin_ids)),reply_markup=admin_menu())

@router.message(F.text=='📢 Xabar yuborish')
async def broadcast_start(m:Message,state:FSMContext,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    await state.set_state(Broadcast.text); await m.answer('📢 Barcha foydalanuvchilarga yuboriladigan xabar matnini yuboring. Bekor qilish: /cancel')

@router.message(Broadcast.text)
async def broadcast(m:Message,state:FSMContext,db,settings,bot):
    if not admin_only(m.from_user.id,settings): return
    users=(await db.session.execute(select(User.telegram_id))).scalars().all(); sent=0; failed=0
    for uid in users:
        try: await bot.send_message(uid,m.text); sent+=1
        except Exception: failed+=1
    await state.clear(); await m.answer(f'📢 Xabar yakunlandi.\n✅ Yuborildi: {sent}\n❌ Xato: {failed}',reply_markup=admin_menu())

@router.message(Command('cancel'))
async def cancel_command(m:Message,state:FSMContext): await state.clear(); await m.answer('❌ Amal bekor qilindi.',reply_markup=admin_menu())

@router.message(F.text=='✏️ Tahrirlash')
async def edit_help(m:Message,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    await m.answer('✏️ Tahrirlash uchun avval “Anime boshqarish”dan anime tanlang, keyin mavjud tahrirlash tugmasidan foydalaning.',reply_markup=admin_menu())

@router.message(F.text=='🗑 O‘chirish')
async def delete_help(m:Message,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    await m.answer('🗑 O‘chirish uchun “Anime boshqarish”dan anime tanlang. Tasdiqlashsiz hech narsa o‘chirilmaydi.',reply_markup=admin_menu())
