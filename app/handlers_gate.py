from aiogram import F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from .access import is_admin
from .keyboards import main_menu

router = Router()


def channel_link(value: str) -> str:
    v = value.strip()
    if v.startswith('http://') or v.startswith('https://'):
        return v
    return 'https://t.me/' + v.lstrip('@')


async def missing_channels(bot, uid: int, settings):
    missing = []
    for ch in settings.mandatory_channels:
        try:
            chat = await bot.get_chat(ch)
            member = await bot.get_chat_member(chat.id, uid)
            if member.status in {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED} or (
                member.status == ChatMemberStatus.RESTRICTED and not getattr(member, 'is_member', False)
            ):
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
    await m.answer(
        '🔒 <b>Majburiy obuna</b>\n\n'
        'Botdan foydalanish uchun quyidagi kanal(lar)ga obuna bo‘ling.\n'
        'Keyin «✅ Tekshirish» tugmasini bosing.',
        reply_markup=gate_keyboard(missing),
    )
    return True


@router.message(Command('start'))
async def start_gate(m: Message, bot, settings, db):
    await db.user.upsert(
        m.from_user.id,
        m.from_user.username,
        m.from_user.first_name,
        is_admin(m.from_user.id, settings),
    )
    if await gate_message(m, bot, settings):
        return
    await m.answer(
        '✨ <b>AniEasy Bot 1.0</b>\n\n🎬 Anime olami siz uchun tayyor!\nKerakli bo‘limni tanlang:',
        reply_markup=main_menu(is_admin(m.from_user.id, settings)),
    )


@router.callback_query(F.data == 'check_subs')
async def check_subs(c: CallbackQuery, bot, settings):
    missing = await missing_channels(bot, c.from_user.id, settings)
    if missing:
        await c.answer('❌ Hali barcha majburiy kanallarga obuna bo‘lmagansiz.', show_alert=True)
        return
    await c.message.edit_text('✅ Obuna tasdiqlandi!')
    await c.message.answer(
        '🏠 <b>AniEasy Bot 1.0</b>\n\nMenyu ochildi:',
        reply_markup=main_menu(is_admin(c.from_user.id, settings)),
    )
    await c.answer()
