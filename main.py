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
from middlewares.outer import (MsgProcMiddleware,
                               RedisMiddleware,
                               ThrottlingMiddleware)

logger_main = logging.getLogger(__name__)


async def setup_logging(config):
    with open('logs/logging_setting/log_config.yml', 'rt') as file:
        config_str = file.read()
    # вставляем(заменяем шаблоны на) переменные окружения
    config_str = config_str.replace('${LOG_LEVEL}', config.level_log)
    log_config = yaml.safe_load(config_str)
    dictConfig(log_config)
    logger_main.info('Loading logging & config success')


async def setup_redis(config: Config) -> tuple[Redis, RedisStorage, Redis]:
    """Настройка Redis для FSM, throttling и данных пользователей."""
    redis_fsm = Redis(host=config.redis_host, port=6379, db=0,
                      decode_responses=True)
    redis_throttling = RedisStorage.from_url(
            f'redis://{config.redis_host}:6379/1')
    redis_data = Redis(host=config.redis_host, port=6379, db=2,
                       decode_responses=True)
    try:
        await redis_fsm.ping()
        logger_main.info("Redis connection established successfully.")
    except Exception as err:
        logger_main.error(f"Error connecting to Redis: {err}")
        raise
    return redis_fsm, redis_throttling, redis_data


async def main():
    config: Config = load_config()
    await setup_logging(config)
    bot = Bot(token=config.tg_bot.token,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # broadcast_redis = RedisSettings(host=config.redis_host, port=6379,
    #                                 database=3)
    redis_fsm, storage_throttling, redis_data = await setup_redis(config)
    storage = RedisStorage(redis=redis_fsm)
    dp = Dispatcher(storage=storage)
    await set_main_menu(bot)

    try:
        # routers
        dp.include_router(admin_handlers.admin_router)
        dp.include_router(user_handlers.user_router)
        dp.include_router(other_handlers.other_router)

        # middlewares
        dp.update.middleware(RedisMiddleware(redis=redis_data))
        dp.update.middleware(MsgProcMiddleware())
        dp.message.outer_middleware(
                ThrottlingMiddleware(storage=storage_throttling, ttl=700))
        dp.callback_query.outer_middleware(
                ThrottlingMiddleware(storage=storage_throttling, ttl=500))

        await bot.delete_webhook(drop_pending_updates=True)
        logger_main.info('Start bot')
        await dp.start_polling(bot, admins=config.tg_bot.id_admins,
                               stepik=config.stepik, w_text=config.w_text)
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
