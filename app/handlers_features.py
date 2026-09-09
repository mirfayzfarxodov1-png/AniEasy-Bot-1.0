from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import func, select
from .models import Anime, Episode, User
from .states import AdminManage
from .keyboards import admin_menu, main_menu

router = Router()

FEATURES = {
    '🔥 Top anime': '🔥 <b>Top anime</b>\n\nBu bo‘lim eng ko‘p ko‘rilgan qismlar asosida top anime ro‘yxatini ko‘rsatadi.',
    '🎲 Tasodifiy': '🎲 <b>Tasodifiy anime</b>\n\nTasodifiy anime tanlash funksiyasi tayyor.',
    '📅 Yangi qismlar': '📅 <b>Yangi qismlar</b>\n\nEng so‘nggi qo‘shilgan qismlar shu yerda chiqadi.',
    '📈 Trend': '📈 <b>Trend</b>\n\nKo‘rishlar bo‘yicha trendlarni ko‘rish mumkin.',
    '🕘 Tarix': '🕘 <b>Tarix</b>\n\nKo‘rilgan qismlar tarixi profilingiz bilan bog‘lanadi.',
    '🏷 Janr bo‘yicha': '🏷 <b>Janr bo‘yicha</b>\n\nJanrlar menyusidan anime tanlang.',
    '🔔 Yangiliklar obunasi': '🔔 <b>Yangiliklar obunasi</b>\n\nYangi anime va qismlar haqida bildirishnoma sozlamasi.',
    '🌟 Premium': '🌟 <b>Premium</b>\n\nPremium bo‘limi hozircha bepul rejimda ochiq.',
    '📌 Saqlangan': '📌 <b>Saqlangan</b>\n\nSevimlilar bo‘limida saqlangan anime chiqadi.',
    '🎯 Tavsiyalar': '🎯 <b>Tavsiyalar</b>\n\nSevimli janrlaringiz asosida tavsiyalar tayyorlanadi.',
    '🧭 Navigatsiya': '🧭 <b>Navigatsiya</b>\n\nAnime → Qism → Keyingi/Oldingi qism orqali tez yurishingiz mumkin.',
    '📊 Bot statistikasi': '📊 <b>Bot statistikasi</b>\n\nStatistika admin panelda real vaqtga yaqin ko‘rinishda mavjud.',
    '📝 So‘rov yuborish': '📝 <b>So‘rov yuborish</b>\n\nKerakli anime nomini keyingi xabarda yozing.',
    '💬 Aloqa': '💬 <b>Aloqa</b>\n\nMuammo yoki taklifingizni administratorga yuborish mumkin.',
    '🎨 Tema': '🎨 <b>Tema</b>\n\nTelegram ilovangizning tema sozlamalari ishlatiladi.',
    '⚡ Tezkor menyu': '⚡ <b>Tezkor menyu</b>\n\nAnime, qidiruv, sevimlilar va davom ettirish eng tez yo‘llardir.',
    '📚 Qo‘llanma': '📚 <b>Qo‘llanma</b>\n\n/start → Anime → anime → Qismlar → kerakli qism.',
    '🆘 Muammo haqida': '🆘 <b>Yordam</b>\n\nVideo ochilmasa qayta urinib ko‘ring yoki administratorga xabar bering.',
}


@router.message(F.text.in_(list(FEATURES.keys())))
async def feature_menu(m: Message, settings):
    await m.answer(FEATURES[m.text], reply_markup=main_menu(m.from_user.id in settings.admin_ids or m.from_user.id == settings.owner_id, settings.webapp_url))


async def owner_only(m, settings):
    if m.from_user.id != settings.owner_id:
        await m.answer('❌ Bu amal faqat bot egasi uchun.')
        return False
    return True


@router.message(F.text == '➕ Admin qo‘shish')
async def add_admin_start(m: Message, state: FSMContext, settings):
    if not await owner_only(m, settings):
        return
    await state.set_state(AdminManage.add_id)
    await m.answer('➕ <b>Admin qo‘shish</b>\n\nYangi adminning Telegram ID raqamini yuboring:')


@router.message(AdminManage.add_id)
async def add_admin_finish(m: Message, state: FSMContext, db, settings):
    if not await owner_only(m, settings):
        await state.clear()
        return
    try:
        uid = int((m.text or '').strip())
    except ValueError:
        return await m.answer('❌ ID faqat raqam bo‘lishi kerak.')
    user = (await db.session.execute(select(User).where(User.telegram_id == uid))).scalar_one_or_none()
    if user:
        user.is_admin = True
        user.last_active = user.last_active
    else:
        user = User(telegram_id=uid, is_admin=True)
        db.session.add(user)
    await db.session.commit()
    await state.clear()
    await m.answer(f'✅ <code>{uid}</code> admin qilib qo‘shildi.', reply_markup=admin_menu())


@router.message(F.text == '➖ Admin chiqarish')
async def remove_admin_start(m: Message, state: FSMContext, settings):
    if not await owner_only(m, settings):
        return
    await state.set_state(AdminManage.remove_id)
    await m.answer('➖ <b>Admin chiqarish</b>\n\nAdminning Telegram ID raqamini yuboring:')


@router.message(AdminManage.remove_id)
async def remove_admin_finish(m: Message, state: FSMContext, db, settings):
    if not await owner_only(m, settings):
        await state.clear()
        return
    try:
        uid = int((m.text or '').strip())
    except ValueError:
        return await m.answer('❌ ID faqat raqam bo‘lishi kerak.')
    if uid == settings.owner_id:
        return await m.answer('❌ Bot egasini adminlikdan chiqarib bo‘lmaydi.')
    user = (await db.session.execute(select(User).where(User.telegram_id == uid))).scalar_one_or_none()
    if not user:
        await state.clear()
        return await m.answer('⚠️ Bu ID bazada topilmadi.', reply_markup=admin_menu())
    user.is_admin = False
    await db.session.commit()
    await state.clear()
    await m.answer(f'✅ <code>{uid}</code> adminlikdan chiqarildi.', reply_markup=admin_menu())
