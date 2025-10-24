import asyncio
import logging
from logging.config import dictConfig

import yaml
from aiogram.fsm.storage.redis import Redis, RedisStorage
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from arq.connections import RedisSettings

from config_data.config import Config, load_config
from keyboards.set_menu import set_main_menu
from handlers import admin_handlers, user_handlers, temp_handlers
from middlewares.outer import (MsgProcMiddleware,
                               RedisMiddleware,
                               ThrottlingMiddleware)
from queues.que_utils import run_arq_worker

logger_main = logging.getLogger(__name__)

async def setup_logging(config: Config):
    with open('logging_setting/log_config.yml', 'rt') as file:
        log_config = yaml.safe_load(file)
    
    # set level log
    log_config['root']['level'] = config.level_log
    for logger_cfg in log_config.get('loggers', {}).values():
        logger_cfg['level'] = config.level_log
    
    # Обновляем Telegram-хэндлеры, если включены
    handlers = log_config.get('handlers', {})
    
    if config.log_tg_cert_enabled:
        if 'telegram_cert' in handlers:
            handlers['telegram_cert']['bot_token'] = config.tg_bot.token
            handlers['telegram_cert']['chat_id'] = config.log_tg_cert_chat_id
            handlers['telegram_cert']['thread_id'] = config.log_tg_cert_thread_id
    else:
        handlers.pop('telegram_cert', None)
    
    if config.log_error_tg_enabled:
        if 'telegram_error' in handlers:
            handlers['telegram_error']['bot_token'] = config.tg_bot.token
            handlers['telegram_error']['chat_id'] = config.log_error_tg_chat_id
            handlers['telegram_error'][
                'thread_id'] = config.log_error_tg_thread_id
    else:
        handlers.pop('telegram_error', None)
    
    # Удаляем ссылки на отключённые хэндлеры из логгеров
    for logger_cfg in log_config.get('loggers', {}).values():
        if 'handlers' in logger_cfg:
            logger_cfg['handlers'] = [h for h in logger_cfg['handlers'] if
                    h in handlers]
    
    # То же самое для root
    if 'handlers' in log_config.get('root', {}):
        log_config['root']['handlers'] = [h for h in
                log_config['root']['handlers'] if h in handlers]
    
    dictConfig(log_config)
    logger_main.info('Loading logging & config success')


async def setup_redis(config: Config) -> tuple[
        Redis, RedisStorage, Redis, RedisSettings]:
    """Настройка Redis для FSM, throttling и данных пользователей."""
    redis_fsm = Redis(host=config.redis_host,
                      port=6379,
                      db=0,
                      decode_responses=True)
    
    redis_throttling = RedisStorage.from_url(f'redis://{config.redis_host}:6379/1')
    
    redis_data = Redis(host=config.redis_host,
                       port=6379,
                       db=2,
                       decode_responses=True)
    
    redis_que = RedisSettings(host=config.redis_host, port=6379, database=3)
    
    try:
        await redis_fsm.ping()
        logger_main.info("Redis connection established successfully.")
    except Exception as err:
        logger_main.error(f"Error connecting to Redis: {err}")
        raise
    return redis_fsm, redis_throttling, redis_data, redis_que


async def main():
    config: Config = load_config()
    await setup_logging(config)
    bot = Bot(token=config.tg_bot.token,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    redis_fsm, storage_throttling, redis_data, redis_que = await setup_redis(
            config)
    
    storage = RedisStorage(redis=redis_fsm)
    dp = Dispatcher(storage=storage)
    
    await set_main_menu(bot)
    
    try:
        # middlewares (register first to wrap entire pipeline)
        # maintenance_middleware = StrictMaintenanceMiddleware(
        #     redis=redis_data, enabled=True,
        # По умолчанию выключено, можно включать через Redis
        # message="⚙️ Бот временно недоступен из-за технических работ. Приносим извинения за неудобства!")
        # dp.update.outer_middleware(maintenance_middleware)
        dp.update.middleware(RedisMiddleware(redis=redis_data))
        dp.update.middleware(MsgProcMiddleware())
        dp.message.outer_middleware(ThrottlingMiddleware(storage=storage_throttling,
                                                         ttl=700))
        dp.callback_query.outer_middleware(ThrottlingMiddleware(storage=storage_throttling,
                                                                ttl=500))
        
        # routers
        dp.include_router(temp_handlers.temp_router)
        dp.include_router(admin_handlers.admin_router)
        dp.include_router(user_handlers.user_router)
        
        await bot.delete_webhook(drop_pending_updates=True)
        logger_main.info('Start bot')
        
        await asyncio.gather(dp.start_polling(bot,
                                              admins=config.tg_bot.id_admins,
                                              stepik=config.stepik,
                                              w_text=config.w_text,
                                              redis_que=redis_que,
                                              tg_target_channel=config.tg_target_channel,
                                              ),
                             run_arq_worker(redis_que, bot=bot))
    
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
