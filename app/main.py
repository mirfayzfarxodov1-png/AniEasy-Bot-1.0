import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import MenuButtonWebApp, WebAppInfo

from .config import load_settings
from .db import Database
from .middlewares import DependenciesMiddleware, RateLimitMiddleware
from .handlers_gate import router as gate_router
from .handlers_webapp import router as webapp_router
from .handlers_admin import router as admin_router
from .handlers_extra import router as extra_router
from .handlers_features import router as features_router
from .handlers_user import router as user_router
from .keyboards import WEBAPP_URL


async def main() -> None:
    settings = load_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logger = logging.getLogger("anieasy")

    db = Database(settings)
    await db.create_tables()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.message.middleware(RateLimitMiddleware())
    dp.callback_query.middleware(RateLimitMiddleware())

    dependencies = DependenciesMiddleware(db, settings)
    dp.message.middleware(dependencies)
    dp.callback_query.middleware(dependencies)

    # Router order: access gate first, then Mini App/admin/features/user handlers.
    dp.include_router(gate_router)
    dp.include_router(webapp_router)
    dp.include_router(admin_router)
    dp.include_router(extra_router)
    dp.include_router(features_router)
    dp.include_router(user_router)

    webapp_url = settings.webapp_url or WEBAPP_URL

    try:
        # Remove stale webhook and pending updates before polling.
        await bot.delete_webhook(drop_pending_updates=False)

        me = await bot.get_me()
        logger.info("AniEasy Bot 1.0 starting: @%s (%s)", me.username, me.id)

        # Telegram chat-menu button: users get a real Web App / Open button.
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Open AniEasy",
                web_app=WebAppInfo(url=webapp_url),
            )
        )

        # Keep the slash-command menu clean; the main UI is the keyboard + Mini App.
        await bot.set_my_commands([])

        logger.info("Mini App: %s", webapp_url)
        logger.info("AniEasy Bot 1.0 online")

        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
