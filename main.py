import asyncio
import warnings
from pytz_deprecation_shim import PytzUsageWarning

from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from tgbot.utils.logger import logger
from tgbot.utils.config import load_config

from tgbot.handlers.menu import register_menu
from tgbot.handlers.admin import register_admin
from tgbot.handlers.scheduler import register_schedulers
from tgbot.filters.admin import AdminFilter
from tgbot.middlewares.throttling import ThrottlingMiddleware
from tgbot.middlewares.apscheduler import SchedulerMiddleware


def register_all_middlewares(dp, scheduler):
    dp.setup_middleware(ThrottlingMiddleware())
    dp.setup_middleware(SchedulerMiddleware(scheduler))


def register_all_filters(dp):
    dp.filters_factory.bind(AdminFilter)


def register_all_handlers(dp, bot, scheduler):
    register_menu(dp)
    register_admin(dp)
    register_schedulers(bot, scheduler)


async def set_commands(bot):
    commands = [
        BotCommand(command="/start", description="Start"),
        BotCommand(command="/menu", description="Menu"),
    ]
    await bot.set_my_commands(commands)


async def main():
    warnings.filterwarnings(action="ignore", category=PytzUsageWarning)
    data_config = load_config()

    logger.info("Starting bot")

    bot = Bot(token=data_config['bot_token'])
    dp = Dispatcher(bot, storage=MemoryStorage())
    scheduler = AsyncIOScheduler(timezone="Asia/Almaty")

    register_all_middlewares(dp, scheduler)
    register_all_filters(dp)
    register_all_handlers(dp, bot, scheduler)

    await set_commands(bot)

    try:
        scheduler.start()
        await dp.start_polling()
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped")
