from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def kb(rows): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t,callback_data=d) for t,d in r] for r in rows])

def main_menu(admin=False):
    rows=[[('🎬 Anime','anime'),('🔎 Qidirish','search')],[('⭐ Sevimlilar','favorites'),('📺 Oxirgi qo‘shilganlar','latest')],[('ℹ️ Yordam','help')]]
    if admin: rows.append([('👑 Admin panel','admin')])
    return kb(rows)

def back_home(): return kb([[('⬅️ Orqaga','back'),('🏠 Bosh menyu','home')]])

def admin_menu(): return kb([[('➕ Anime qo‘shish','admin_add'),('📚 Anime ro‘yxati','admin_animes')],[('📊 Statistika','admin_stats'),('⚙️ Sozlamalar','admin_settings')],[('💾 Backup','admin_backup'),('📢 Xabar yuborish','admin_broadcast')],[('🏠 Bosh menyu','home')]])

def anime_actions(aid, favorite=True): return kb([[('📺 Qismlar',f'episodes:{aid}:0'),('✏️ Tahrirlash',f'edit_anime:{aid}')],[('⭐ Sevimli' if favorite else '☆ Sevimlidan chiqarish',f'fav:{aid}')],[('🗑 O‘chirish',f'del_anime:{aid}')],[('⬅️ Orqaga','back')]])

def episodes_page(aid, episodes, page, size):
    rows=[]
    row=[]
    for e in episodes:
        row.append((f'{e.episode_number}-qism',f'episode:{aid}:{e.episode_number}'))
        if len(row)==2: rows.append(row); row=[]
    if row: rows.append(row)
    nav=[]
    if page>0: nav.append(('⬅️','ep_page:%d:%d'%(aid,page-1)))
    if len(episodes)==size: nav.append(('➡️','ep_page:%d:%d'%(aid,page+1)))
    if nav: rows.append(nav)
    rows.append([('🏠 Bosh menyu','home')]); return kb(rows)

def episode_nav(aid, prev_num, next_num):
    row=[]
    if prev_num: row.append((f'⬅️ {prev_num}-qism',f'episode:{aid}:{prev_num}'))
    row.append(('🏠 Anime',f'anime:{aid}'))
    if next_num: row.append((f'{next_num}-qism ➡️',f'episode:{aid}:{next_num}'))
    return kb([row])
