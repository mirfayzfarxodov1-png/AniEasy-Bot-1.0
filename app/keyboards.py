from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo


def ikb(rows):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=d) for t, d in row] for row in rows])


def main_menu(admin=False, webapp_url=None):
    rows = [
        [KeyboardButton(text='🎬 Anime'), KeyboardButton(text='🔎 Qidirish')],
        [KeyboardButton(text='⭐ Sevimlilar'), KeyboardButton(text='🆕 Yangiliklar')],
        [KeyboardButton(text='🎭 Janrlar'), KeyboardButton(text='📺 Davom ettirish')],
        [KeyboardButton(text='👤 Profil'), KeyboardButton(text='ℹ️ Yordam')],
    ]
    if webapp_url:
        rows.append([KeyboardButton(text='🌐 AniEasy Web', web_app=WebAppInfo(url=webapp_url))])
    if admin:
        rows.append([KeyboardButton(text='👑 Admin panel')])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, is_persistent=True, input_field_placeholder='Bo‘limni tanlang…')


def admin_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='➕ Anime qo‘shish'), KeyboardButton(text='📚 Anime boshqarish')],
        [KeyboardButton(text='📺 Qismlar'), KeyboardButton(text='✏️ Tahrirlash')],
        [KeyboardButton(text='🗑 O‘chirish'), KeyboardButton(text='📊 Statistika')],
        [KeyboardButton(text='👥 Foydalanuvchilar'), KeyboardButton(text='📢 Xabar yuborish')],
        [KeyboardButton(text='⚙️ Sozlamalar'), KeyboardButton(text='💾 Backup')],
        [KeyboardButton(text='📣 Kanal'), KeyboardButton(text='🛡 Adminlar')],
        [KeyboardButton(text='🏠 Bosh menyu')],
    ], resize_keyboard=True, is_persistent=True, input_field_placeholder='Admin funksiyasini tanlang…')


def inline_home(admin=False):
    rows = [[('🎬 Anime', 'anime'), ('🔎 Qidirish', 'search')], [('⭐ Sevimlilar', 'favorites'), ('🆕 Yangiliklar', 'latest')], [('🎭 Janrlar', 'genres'), ('📺 Davom ettirish', 'continue')], [('👤 Profil', 'profile'), ('ℹ️ Yordam', 'help')]]
    if admin: rows.append([('👑 Admin panel', 'admin')])
    return ikb(rows)


def anime_actions(aid, favorite=True):
    return ikb([[('📺 Qismlar', f'episodes:{aid}:0'), ('⭐ Sevimli' if favorite else '☆ Sevimlidan chiqarish', f'fav:{aid}')], [('✏️ Tahrirlash', f'edit_anime:{aid}'), ('🗑 O‘chirish', f'del_anime:{aid}')], [('⬅️ Orqaga', 'anime'), ('🏠 Bosh menyu', 'home')]])


def episodes_page(aid, episodes, page, size):
    rows=[]; row=[]
    for e in episodes:
        row.append((f'📺 {e.episode_number}-qism', f'episode:{aid}:{e.episode_number}'))
        if len(row)==2: rows.append(row); row=[]
    if row: rows.append(row)
    nav=[]
    if page>0: nav.append(('⬅️', f'ep_page:{aid}:{page-1}'))
    if len(episodes)==size: nav.append(('➡️', f'ep_page:{aid}:{page+1}'))
    if nav: rows.append(nav)
    rows.append([('⬅️ Anime', f'anime:{aid}'), ('🏠 Bosh menyu','home')])
    return ikb(rows)


def episode_nav(aid, prev_num, next_num):
    row=[]
    if prev_num: row.append((f'⬅️ {prev_num}', f'episode:{aid}:{prev_num}'))
    row.append(('🎬 Anime', f'anime:{aid}'))
    if next_num: row.append((f'{next_num} ➡️', f'episode:{aid}:{next_num}'))
    return ikb([row, [('⭐ Sevimliga', f'fav:{aid}'), ('🏠 Bosh menyu','home')]])
