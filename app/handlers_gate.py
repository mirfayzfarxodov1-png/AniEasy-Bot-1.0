from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatMemberStatus
from .keyboards import main_menu, inline_home
from .access import is_admin

router = Router()


def channel_link(value: str) -> str:
    v = value.strip()
    if v.startswith('https://'):
        return v
    return 'https://t.me/' + v.lstrip('@')


async def missing_channels(bot, uid: int, settings):
    missing = []
    for ch in settings.mandatory_channels:
        try:
            chat = await bot.get_chat(ch)
            member = await bot.get_chat_member(chat.id, uid)
            if member.status in {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED, ChatMemberStatus.RESTRICTED} and not getattr(member, 'is_member', False):
                missing.append((chat.title or ch, channel_link(ch)))
        except Exception:
            missing.append((ch, channel_link(ch)))
    return missing


def gate_keyboard(missing):
    rows = [[InlineKeyboardButton(text=f'📢 {name}', url=url)] for name, url in missing]
    rows.append([InlineKeyboardButton(text='✅ Tekshirish', callback_data='check_subs')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def gate_message(m: Message, bot, settings):
    missing = await missing_channels(bot, m.from_user.id, settings)
    if not missing:
        return False
    await m.answer('🔒 <b>Botdan foydalanish uchun avval majburiy kanallarga obuna bo‘ling.</b>\n\nObuna bo‘lgach, «Tekshirish» tugmasini bosing.', reply_markup=gate_keyboard(missing))
    return True


@router.message(Command('start'))
async def start_gate(m: Message, bot, settings, db):
    await db.user.upsert(m.from_user.id, m.from_user.username, m.from_user.first_name, is_admin(m.from_user.id, settings))
    if await gate_message(m, bot, settings):
        return
    await m.answer('✨ <b>AniEasy Bot 1.0</b>\n\n🎬 Anime olami siz uchun tayyor!\n\nKerakli bo‘limni tanlang:', reply_markup=main_menu(is_admin(m.from_user.id, settings)))


@router.callback_query(F.data == 'check_subs')
async def check_subs(c: CallbackQuery, bot, settings):
    missing = await missing_channels(bot, c.from_user.id, settings)
    if missing:
        return await c.answer('❌ Hali barcha kanallarga obuna bo‘lmagansiz.', show_alert=True)
    await c.message.edit_text('✅ Obuna tasdiqlandi! Endi botdan foydalanishingiz mumkin.')
    await c.message.answer('🏠 <b>AniEasy Bot 1.0</b>\n\nMenyu ochildi:', reply_markup=main_menu(is_admin(c.from_user.id, settings)))
    await c.answer()


EXTRA = {
    '🔥 Top anime': '🔥 <b>Top anime</b>\n\nEng ko‘p ko‘rilgan anime ro‘yxati tez orada kengayadi.',
    '🎲 Tasodifiy': '🎲 <b>Tasodifiy anime</b>\n\nAnime katalogidan tasodifiy tanlash bo‘limi.',
    '📅 Yangi qismlar': '📅 <b>Yangi qismlar</b>\n\nYaqinda qo‘shilgan qismlar shu yerda ko‘rsatiladi.',
    '📈 Trend': '📈 <b>Trend</b>\n\nHozirgi mashhur kontentlar shu bo‘limda.',
    '🕘 Tarix': '🕘 <b>Tarix</b>\n\nKo‘rish tarixi «Davom ettirish» orqali saqlanadi.',
    '🏷 Janr bo‘yicha': '🏷 <b>Janr bo‘yicha</b>\n\nJanrlar bo‘limidan kerakli janrni tanlang.',
    '🔔 Yangiliklar': '🔔 <b>Yangiliklar</b>\n\nYangi anime va qismlar haqidagi xabarlar shu yerda.',
    '🌟 Premium': '🌟 <b>Premium</b>\n\nPremium imkoniyatlar bo‘limi.',
    '📌 Saqlangan': '📌 <b>Saqlangan</b>\n\nSevimli anime’laringiz shu yerda.',
    '🎯 Tavsiyalar': '🎯 <b>Tavsiyalar</b>\n\nJanr va ko‘rishlaringiz asosida tavsiyalar.',
    '📊 Bot statistikasi': '📊 <b>Bot statistikasi</b>\n\nAniEasy platformasi faol ishlamoqda.',
    '📝 So‘rov yuborish': '📝 <b>So‘rov yuborish</b>\n\nKerakli anime nomini adminlarga yuboring.',
    '💬 Aloqa': '💬 <b>Aloqa</b>\n\nAdmin bilan bog‘lanish uchun /admin buyrug‘idan foydalaning.',
    '🎨 Tema': '🎨 <b>Tema</b>\n\nAniEasy premium qorong‘i interfeysdan foydalanadi.',
    '⚡ Tezkor menyu': '⚡ <b>Tezkor menyu</b>\n\nAnime → Qidirish → Sevimlilar → Yangiliklar.',
    '📚 Qo‘llanma': '📚 <b>Qo‘llanma</b>\n\nAnime tanlang → qismni bosing → tomosha qiling.',
    '🆘 Muammo': '🆘 <b>Muammo haqida</b>\n\nBot javob bermasa /start ni qayta yuboring yoki admin bilan bog‘laning.',
}


@router.message(F.text.in_(list(EXTRA.keys())))
async def extra_menu(m: Message, settings):
    await m.answer(EXTRA[m.text], reply_markup=main_menu(is_admin(m.from_user.id, settings)))
