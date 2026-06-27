import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from cinedive.app.bot.handlers import setup_routers
from cinedive.app.bot.middlewares.db import DbSessionMiddleware
from cinedive.app.config import Settings, get_settings
from cinedive.app.database.session import async_session_factory, dispose_engine


def create_bot(settings: Settings) -> Bot:
    return Bot(
        token=settings.require_bot_token(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.update.middleware(DbSessionMiddleware(async_session_factory))
    setup_routers(dispatcher)
    return dispatcher


async def health_check(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def run_polling(bot: Bot, dispatcher: Dispatcher) -> None:
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        await dispose_engine()


async def register_webhook(bot: Bot, dispatcher: Dispatcher, settings: Settings) -> None:
    await bot.set_webhook(
        url=settings.webhook_url,
        secret_token=settings.require_webhook_secret(),
        allowed_updates=dispatcher.resolve_used_update_types(),
    )


async def close_resources(bot: Bot) -> None:
    await bot.session.close()
    await dispose_engine()


def create_webhook_app(bot: Bot, dispatcher: Dispatcher, settings: Settings) -> web.Application:
    app = web.Application()
    app.router.add_get("/health", health_check)

    SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
        secret_token=settings.require_webhook_secret(),
    ).register(app, path=settings.normalized_webhook_path)

    setup_application(app, dispatcher, bot=bot)
    app.on_startup.append(lambda _: register_webhook(bot, dispatcher, settings))
    app.on_shutdown.append(lambda _: close_resources(bot))
    return app


async def main() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())

    bot = create_bot(settings)
    dispatcher = create_dispatcher()

    if settings.bot_mode == "polling":
        await run_polling(bot, dispatcher)
        return

    app = create_webhook_app(bot, dispatcher, settings)
    runner = web.AppRunner(app)
    try:
        await runner.setup()
        site = web.TCPSite(runner, settings.web_server_host, settings.web_server_port)
        await site.start()
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
