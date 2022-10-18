import asyncio
import logging
import warnings

from pytz_deprecation_shim import PytzUsageWarning
from datetime import date
import calendar
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from tgbot.config import load_config
from tgbot.filters.admin import IsAdmin
from tgbot.handlers.admin import register_admin
from tgbot.handlers.user import register_user
from tgbot.handlers.menu import register_menu, register_callback_menu
from tgbot.handlers.menu import data_timetable
from tgbot.handlers.echo import register_echo
from tgbot.middlewares.environment import EnvironmentMiddleware
from tgbot.middlewares.scheduler import SchedulerMiddleware

logger = logging.getLogger(__name__)


def register_all_middlewares(dp, config):
    dp.setup_middleware(EnvironmentMiddleware(config=config))
    dp.setup_middleware(SchedulerMiddleware(config))


def register_all_filters(dp):
    dp.filters_factory.bind(IsAdmin)


def register_all_handlers(dp):
    register_admin(dp)
    register_user(dp)
    register_menu(dp)
    register_callback_menu(dp)
    register_echo(dp)


async def daily_notify(bot, config):
    my_date = calendar.day_name[date.today().weekday()].lower()
    for admin_id in config.tg_bot.admin_ids:
        await bot.send_message(chat_id=admin_id, text=f"Daily notify!!!\n\n"
                                                      f"Your timetable on {my_date[0].upper() + my_date[1:]}:\n\n"
                                                      f"{data_timetable[my_date]}")


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )
    logger.info("Starting bot")
    config = load_config(".env")

    storage = RedisStorage2() if config.tg_bot.use_redis else MemoryStorage()
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    dp = Dispatcher(bot, storage=storage)

    warnings.filterwarnings(action="ignore", category=PytzUsageWarning)
    scheduler = AsyncIOScheduler()

    bot['config'] = config

    register_all_middlewares(dp, config)
    register_all_filters(dp)
    register_all_handlers(dp)

    # set_scheduled_jobs(scheduler, bot)
    scheduler.add_job(daily_notify, 'cron', day_of_week='mon-sat', hour=7, minute=0,
                      args=(bot, config))

    # start
    try:
        scheduler.start()
        await dp.start_polling()
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
