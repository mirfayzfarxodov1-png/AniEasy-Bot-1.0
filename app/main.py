import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from .config import load_settings
from .db import Database
from .middlewares import DependenciesMiddleware, RateLimitMiddleware
from .handlers_gate import router as gate_router
from .handlers_user import router as user_router
from .handlers_admin import router as admin_router
from .handlers_extra import router as extra_router
from .handlers_features import router as features_router

async def main():
    settings = load_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO), format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
    db = Database(settings)
    await db.create_tables()
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.message.middleware(RateLimitMiddleware())
    dp.callback_query.middleware(RateLimitMiddleware())
    dep = DependenciesMiddleware(db, settings)
    dp.message.middleware(dep)
    dp.callback_query.middleware(dep)
    dp.include_router(gate_router)
    dp.include_router(admin_router)
    dp.include_router(extra_router)
    dp.include_router(features_router)
    dp.include_router(user_router)
    # Remove Telegram's slash-command menu. Navigation is provided by the bot's own keyboard.
    await bot.set_my_commands([])
    try:
        await bot.delete_webhook(drop_pending_updates=False)
        me = await bot.get_me()
        logging.info('AniEasy Bot 1.0 online: @%s (id=%s)', me.username, me.id)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await db.close()
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())
