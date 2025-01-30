import asyncio
import logging
from logging.config import dictConfig

import yaml
from aiogram.fsm.storage.redis import Redis, RedisStorage
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config_data.config import Config, load_config
from keyboards.set_menu import set_main_menu
from handlers import admin_handlers, other_handlers, user_handlers
from middlewares.outer import (RedisMiddleware,
                               ThrottlingMiddleware,
                               TimingMiddleware)

logger_main = logging.getLogger(__name__)


async def main():
    with open('logs/logging_setting/log_config.yml', 'rt') as file:
        log_config = yaml.safe_load(file.read())
    dictConfig(log_config)
    logger_main.info('Loading logging settings success')

    config: Config = load_config()
    bot = Bot(token=config.tg_bot.token,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Redis for FSM (db=0)
    redis_fsm = Redis(host=config.redis_host, port=6379, db=0,
                   decode_responses=True)
    storage = RedisStorage(redis=redis_fsm)

    # Redis for throttling storage (db=1)
    storage_throttling = RedisStorage.from_url(
            f'redis://{config.redis_host}:6379/1')

    # Redis for user data (db=2)
    redis_data = Redis(host=config.redis_host, port=6379, db=2,
                       decode_responses=True)

    try:
        await redis_fsm.ping()
        logger_main.info("Redis connection established successfully.")
    except Exception as err:
        logger_main.error(f"Error connecting to Redis: {err}")
        raise

    dp = Dispatcher(storage=storage)

    try:
        logger_main.info('Loading from a db.json success')

        await set_main_menu(bot)

        # routers
        dp.include_router(admin_handlers.admin_router)
        dp.include_router(user_handlers.user_router)
        dp.include_router(other_handlers.other_router)

        # middlewares
        dp.message.middleware(TimingMiddleware())
        dp.update.middleware(RedisMiddleware(redis=redis_data))
        dp.message.outer_middleware(
                ThrottlingMiddleware(storage=storage_throttling, ttl=700))
        dp.callback_query.outer_middleware(
                ThrottlingMiddleware(storage=storage_throttling, ttl=500))

        await bot.delete_webhook(drop_pending_updates=True)
        logger_main.info('Start bot')
        await dp.start_polling(bot, admins=config.tg_bot.id_admins,
                               stepik=config.stepik)
    except Exception as err:
        logger_main.exception(err)
        raise

    finally:
        await redis_fsm.aclose()
        await redis_data.aclose()
        await storage_throttling.redis.aclose()
        logger_main.info('Stop bot')


if __name__ == "__main__":
    asyncio.run(main())
