import re
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatMemberStatus
from sqlalchemy import func, select
from .states import AddAnime, Upload, Broadcast, EditAnime, AdminManage, Post
from .keyboards import admin_menu, ikb, url_ikb
from .services import parse_episode
from .models import Episode, User
from .access import is_admin, is_owner, add_admin, remove_admin

router=Router()
def admin_only(uid,settings): return is_admin(uid,settings)
def deny(m): return m.answer('❌ Bu bo‘lim faqat adminlar uchun.')
def panel_text(): return '👑 <b>AniEasy Admin Panel</b>\n\nBoshqaruv bo‘limini tanlang:'

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
async def add_start(m:Message,state:FSMContext,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    await state.set_state(AddAnime.title); await m.answer('➕ <b>Anime qo‘shish</b>\n\nAnime nomini yuboring:')

@router.message(AddAnime.title)
async def add_title(m:Message,state:FSMContext,db,settings):
    if not admin_only(m.from_user.id,settings): return
    title=(m.text or '').strip()
    if not title: return await m.answer('❌ Anime nomi bo‘sh bo‘lishi mumkin emas.')
    old=await db.anime.search(title,1)
    if old and old[0].title.lower()==title.lower(): return await m.answer('⚠️ Bu anime allaqachon mavjud.')
    a=await db.anime.create(title=title); await state.set_state(Upload.episodes); await state.update_data(anime_id=a.id,next_episode=1)
    await m.answer(f'✅ <b>{a.title}</b> yaratildi.\n\n🎞 Videolarni ketma-ket yuboring. Captiondagi <code>7-qism</code> avtomatik aniqlanadi.',reply_markup=ikb([[('⏭ Yakunlash','upload_finish'),('❌ Bekor qilish','upload_cancel')]]))

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
async def replace(c:CallbackQuery,state:FSMContext,db,settings):
    if not admin_only(c.from_user.id,settings): return await c.answer('❌ Ruxsat yo‘q.',show_alert=True)
    d=await state.get_data(); old=await db.episodes.get(d.get('anime_id'),int(c.data.split(':')[1]))
    if not old: return await c.answer('Qism topilmadi.',show_alert=True)
    await db.episodes.replace(old,telegram_file_id=d['pending_file_id'],file_unique_id=d['pending_unique_id'],caption=d['pending_caption']); n=int(c.data.split(':')[1]); await state.update_data(next_episode=n+1); await c.message.edit_text(f'✅ {n}-qism yangilandi.'); await c.answer()

@router.callback_query(F.data=='replace_cancel')
async def replace_cancel(c:CallbackQuery,state:FSMContext): await state.clear(); await c.message.edit_text('❌ Yangilash bekor qilindi.'); await c.answer()

@router.message(F.text=='📚 Anime boshqarish')
async def admin_animes(m:Message,db,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    items=await db.anime.list(0,settings.pagination_size); text='📚 <b>Anime boshqaruvi</b>\n\n'+('Ro‘yxat bo‘sh.' if not items else '\n'.join(f'• {a.title} — {await db.episodes.count(a.id)} qism' for a in items)); await m.answer(text,reply_markup=ikb([[(f'🎬 {a.title}',f'anime:{a.id}')] for a in items]+[[('🏠 Admin','admin')]]))

@router.message(F.text=='📺 Qismlar')
async def episode_manager(m:Message,db,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    items=await db.anime.list(0,settings.pagination_size); await m.answer('📺 <b>Anime qismini tanlang:</b>',reply_markup=ikb([[(a.title,f'episodes:{a.id}:0')] for a in items]+[[('👑 Admin','admin')]]))

@router.message(F.text=='📊 Statistika')
async def stats(m:Message,db,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    ac=await db.anime.count(); ec=(await db.session.execute(select(func.count()).select_from(Episode))).scalar_one(); uc=(await db.session.execute(select(func.count()).select_from(User))).scalar_one(); views=(await db.session.execute(select(func.coalesce(func.sum(Episode.views),0)))).scalar_one(); await m.answer(f'📊 <b>Bot statistikasi</b>\n\n👥 Foydalanuvchilar: {uc}\n🎬 Anime: {ac}\n📺 Qismlar: {ec}\n👁 Ko‘rishlar: {views}',reply_markup=admin_menu())

@router.message(F.text=='👥 Foydalanuvchilar')
async def users(m:Message,db,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    rows=(await db.session.execute(select(User).order_by(User.last_active.desc()).limit(15))).scalars().all(); await m.answer('👥 <b>Oxirgi foydalanuvchilar</b>\n\n'+('\n'.join(f'• {u.first_name or "Noma’lum"} — <code>{u.telegram_id}</code>' for u in rows) if rows else 'Foydalanuvchi yo‘q.'),reply_markup=admin_menu())

@router.message(F.text=='⚙️ Sozlamalar')
async def settings_page(m:Message,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    await m.answer(f'⚙️ <b>Sozlamalar</b>\n\n📄 Shablon: <code>{settings.description_template}</code>\n📄 Limit: {settings.pagination_size}\n📢 Kanal: {settings.channel_id or "o‘rnatilmagan"}\n🔒 Majburiy kanallar: {len(settings.mandatory_channels)}')

@router.message(F.text=='💾 Backup')
async def backup(m:Message,db,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    await m.answer(f'💾 <b>Backup nazorati</b>\n\nAnime: {await db.anime.count()}\nQismlar: '+str((await db.session.execute(select(func.count()).select_from(Episode))).scalar_one()),reply_markup=admin_menu())

@router.message(F.text=='📣 Kanal')
async def channel(m:Message,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    await m.answer(f'📣 <b>Kanal sozlamalari</b>\n\nCHANNEL_ID: {settings.channel_id or "yo‘q"}\nMajburiy: {", ".join(settings.mandatory_channels) or "yo‘q"}',reply_markup=admin_menu())

@router.message(F.text=='🛡 Adminlar')
async def admins(m:Message,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    from .access import RUNTIME_ADMINS
    await m.answer('🛡 <b>Adminlar</b>\n\nKonfiguratsiya: '+(', '.join(map(str,settings.admin_ids)) or 'yo‘q')+'\nRuntime: '+(', '.join(map(str,RUNTIME_ADMINS)) or 'yo‘q'),reply_markup=admin_menu())

@router.message(F.text=='➕ Admin qo‘shish')
async def add_admin_start(m:Message,state:FSMContext,settings):
    if not is_owner(m.from_user.id,settings): return await deny(m)
    await state.set_state(AdminManage.add_id); await m.answer('➕ Yangi adminning Telegram ID sini yuboring:')

@router.message(AdminManage.add_id)
async def add_admin_value(m:Message,state:FSMContext,settings):
    if not is_owner(m.from_user.id,settings): return
    try: uid=int((m.text or '').strip())
    except ValueError: return await m.answer('❌ ID faqat raqam bo‘lishi kerak.')
    add_admin(uid); await state.clear(); await m.answer(f'✅ {uid} admin qilindi.',reply_markup=admin_menu())

@router.message(F.text=='➖ Admin chiqarish')
async def remove_admin_start(m:Message,state:FSMContext,settings):
    if not is_owner(m.from_user.id,settings): return await deny(m)
    await state.set_state(AdminManage.remove_id); await m.answer('➖ Adminning Telegram ID sini yuboring:')

@router.message(AdminManage.remove_id)
async def remove_admin_value(m:Message,state:FSMContext,settings):
    if not is_owner(m.from_user.id,settings): return
    try: uid=int((m.text or '').strip())
    except ValueError: return await m.answer('❌ ID faqat raqam bo‘lishi kerak.')
    remove_admin(uid); await state.clear(); await m.answer(f'✅ {uid} runtime adminlardan chiqarildi.',reply_markup=admin_menu())

@router.message(F.text=='📢 Xabar yuborish')
async def broadcast_start(m:Message,state:FSMContext,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    await state.set_state(Broadcast.text); await m.answer('📢 Barcha foydalanuvchilarga yuboriladigan xabarni yuboring. /cancel')

@router.message(Broadcast.text)
async def broadcast(m:Message,state:FSMContext,db,settings,bot):
    if not admin_only(m.from_user.id,settings): return
    users=(await db.session.execute(select(User.telegram_id))).scalars().all(); sent=failed=0
    for uid in users:
        try: await bot.send_message(uid,m.text or ''); sent+=1
        except Exception: failed+=1
    await state.clear(); await m.answer(f'📢 Yakunlandi.\n✅ {sent}\n❌ {failed}',reply_markup=admin_menu())

@router.message(F.text=='📢 Post qilish')
async def post_start(m:Message,state:FSMContext,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    await state.set_state(Post.target); await m.answer('📢 <b>Post qilish</b>\n\nKanal yoki guruh @username, t.me/... yoki chat ID sini yuboring.\n\n⚠️ Bot o‘sha chatda admin bo‘lishi shart.')

async def resolve_chat(bot,target):
    target=target.strip()
    if 't.me/' in target: target='@'+target.split('t.me/',1)[1].strip('/').split('/',1)[0]
    if target and not target.startswith('@') and not target.lstrip('-').isdigit(): target='@'+target
    return await bot.get_chat(target)

async def bot_is_admin(bot,chat):
    me=await bot.get_me(); member=await bot.get_chat_member(chat.id,me.id)
    return member.status in {ChatMemberStatus.ADMINISTRATOR,ChatMemberStatus.CREATOR}

@router.message(Post.target)
async def post_target(m:Message,state:FSMContext,settings,bot):
    if not admin_only(m.from_user.id,settings): return
    try:
        chat=await resolve_chat(bot,m.text or '')
        if chat.type not in {'channel','group','supergroup'}: return await m.answer('❌ Faqat kanal yoki guruhga post qilish mumkin.')
        if not await bot_is_admin(bot,chat): return await m.answer('❌ Bot bu chatda admin emas. Avval botga administrator huquqi bering.')
    except Exception:
        return await m.answer('❌ Chat topilmadi yoki tekshirib bo‘lmadi. Public @username, t.me link yoki chat ID yuboring.')
    await state.update_data(target_id=chat.id,target_title=chat.title,target_username=chat.username,target_type=chat.type); await state.set_state(Post.content)
    await m.answer(f'✅ <b>{chat.title}</b> tasdiqlandi.\n\nEndi post matnini yoki video/rasmni caption bilan yuboring:')

@router.message(Post.content)
async def post_content(m:Message,state:FSMContext,settings,bot):
    if not admin_only(m.from_user.id,settings): return
    d=await state.get_data(); chat_id=d.get('target_id'); title=d.get('target_title','Chat'); username=d.get('target_username')
    try:
        if m.video: sent=await bot.send_video(chat_id,m.video.file_id,caption=m.caption or '🎬 AniEasy')
        elif m.photo: sent=await bot.send_photo(chat_id,m.photo[-1].file_id,caption=m.caption or '')
        elif m.text: sent=await bot.send_message(chat_id,m.text)
        else: return await m.answer('❌ Matn, rasm yoki video yuboring.')
        post_link=f'https://t.me/{username}/{sent.message_id}' if username else None
        me=await bot.get_me(); bot_link=f'https://t.me/{me.username}' if me.username else None
        rows=[]
        if bot_link: rows.append([('▶️ Tomosha qilish',bot_link)])
        if bot_link: rows.append([('🤖 Asosiy botga o‘tish',bot_link)])
        if post_link: rows.append([('🔗 Postni ochish',post_link)])
        await state.clear(); await m.answer(f'🎉 <b>Post joylandi!</b>\n📍 {title}',reply_markup=url_ikb(rows) if rows else None)
    except Exception:
        await m.answer('❌ Post yuborilmadi. Bot chatda admin va post yuborish huquqiga ega ekanini tekshiring.')

@router.message(Command('cancel'))
async def cancel_command(m:Message,state:FSMContext): await state.clear(); await m.answer('❌ Amal bekor qilindi.',reply_markup=admin_menu())

@router.message(F.text=='✏️ Tahrirlash')
async def edit_help(m:Message,db,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    items=await db.anime.list(0,settings.pagination_size); await m.answer('✏️ <b>Tahrirlash:</b>',reply_markup=ikb([[(a.title,f'edit_anime:{a.id}')] for a in items]+[[('👑 Admin','admin')]]))

@router.message(F.text=='🗑 O‘chirish')
async def delete_help(m:Message,db,settings):
    if not admin_only(m.from_user.id,settings): return await deny(m)
    items=await db.anime.list(0,settings.pagination_size); await m.answer('🗑 <b>O‘chirish:</b>',reply_markup=ikb([[(a.title,f'del_anime:{a.id}')] for a in items]+[[('👑 Admin','admin')]]))
