from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

WEBAPP_URL = 'https://mirfayzfarxodov1-png.github.io/AniEasy-Bot-1.0/'

def ikb(rows):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=d) for t, d in row] for row in rows])

def url_ikb(rows):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, url=u) for t, u in row] for row in rows])

def main_menu(admin=False, webapp_url=WEBAPP_URL):
    rows = [
        [KeyboardButton(text='🌐 AniEasy Mini App', web_app=WebAppInfo(url=webapp_url))],
        [KeyboardButton(text='🎬 Anime'), KeyboardButton(text='🔎 Qidirish')],
        [KeyboardButton(text='⭐ Sevimlilar'), KeyboardButton(text='🆕 Yangiliklar')],
        [KeyboardButton(text='🎭 Janrlar'), KeyboardButton(text='📺 Davom ettirish')],
        [KeyboardButton(text='🔥 Top anime'), KeyboardButton(text='🎲 Tasodifiy')],
        [KeyboardButton(text='📅 Yangi qismlar'), KeyboardButton(text='📈 Trend')],
        [KeyboardButton(text='🕘 Tarix'), KeyboardButton(text='🎯 Tavsiyalar')],
        [KeyboardButton(text='📌 Saqlangan'), KeyboardButton(text='📊 Bot statistikasi')],
        [KeyboardButton(text='📝 So‘rov yuborish'), KeyboardButton(text='💬 Aloqa')],
        [KeyboardButton(text='⚡ Tezkor menyu'), KeyboardButton(text='📚 Qo‘llanma')],
        [KeyboardButton(text='🆘 Muammo'), KeyboardButton(text='👤 Profil')],
    ]
    if admin: rows.append([KeyboardButton(text='👑 Admin panel')])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, is_persistent=True, input_field_placeholder='Bo‘limni tanlang…')

def admin_menu():
    rows = [
        [('➕ Anime qo‘shish', 'admin_add'), ('📚 Anime boshqarish', 'admin_animes')],
        [('📺 Qismlar', 'admin_eps'), ('✏️ Tahrirlash', 'admin_edit')],
        [('🗑 O‘chirish', 'admin_delete'), ('📊 Statistika', 'admin_stats')],
        [('👥 Foydalanuvchilar', 'admin_users'), ('📢 Xabar yuborish', 'admin_broadcast')],
        [('⚙️ Sozlamalar', 'admin_settings'), ('💾 Backup', 'admin_backup')],
        [('📣 Kanal', 'admin_channel'), ('🛡 Adminlar', 'admin_list')],
        [('➕ Admin qo‘shish', 'admin_add_user'), ('➖ Admin chiqarish', 'admin_remove_user')],
        [('📢 Post qilish', 'post_menu'), ('🏠 Bosh menyu', 'home')],
    ]
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=t) for t, _ in row] for row in rows], resize_keyboard=True, is_persistent=True, input_field_placeholder='Admin funksiyasini tanlang…')

def inline_home(admin=False):
    rows = [[('🎬 Anime', 'anime'), ('🔎 Qidirish', 'search')], [('⭐ Sevimlilar', 'favorites'), ('🆕 Yangiliklar', 'latest')], [('🎭 Janrlar', 'genres'), ('📺 Davom ettirish', 'continue')], [('👤 Profil', 'profile'), ('ℹ️ Yordam', 'help')], [('⚡ Tezkor menyu', 'quick')]]
    if admin: rows.append([('👑 Admin panel', 'admin')])
    return ikb(rows)

def anime_actions(aid, favorite=True):
    return ikb([[('📺 Qismlar', f'episodes:{aid}:0'), ('⭐ Sevimli' if favorite else '☆ Sevimlidan chiqarish', f'fav:{aid}')], [('⬅️ Orqaga', 'anime'), ('🏠 Bosh menyu', 'home')]])

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
