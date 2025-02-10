import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import (TelegramRetryAfter,
                                TelegramBadRequest,
                                TelegramUnauthorizedError)
from arq import create_pool, Worker
from arq.connections import RedisSettings

from utils import get_username

queue_logger = logging.getLogger(__name__)

async def safe_send_message(ctx: dict,
                            user_id: int,
                            message: str,
                            retries=3) -> bool:
    """
    Асинхронно отправляет сообщение с обработкой ошибок и повторными попытками.
    """
    bot = ctx['bot']

    for attempt in range(1, retries + 1):
        try:
            await bot.send_message(chat_id=user_id, text=message)
            queue_logger.info(f"Message sent to {user_id}")
            return True

        except TelegramRetryAfter as e:
            wait_time = e.retry_after
            queue_logger.warning(f"Ограничение лимита для {user_id}. "
                           f"Повтор {attempt}/{retries}. Ожидание "
                                 f"{wait_time}s", exc_info=True)
            await asyncio.sleep(wait_time)

        except (TelegramUnauthorizedError, TelegramBadRequest) as e:
            queue_logger.error(f"Постоянная ошибка для {user_id}: {e}",
                               exc_info=True)
            return False  # Нет смысла повторять при этих ошибках

        except Exception as e:
            queue_logger.error(
                    f"Попытка {attempt}/{retries} не удача {user_id}:"
                    f" {str(e)}",
                    exc_info=True)
            if attempt < retries:
                await asyncio.sleep(2 ** attempt)  # Экспоненциальная задержка

    queue_logger.error(f"Failed to send to {user_id} after {retries} attempts",
                       exc_info=True)
    return False

async def add_mailing_task(redis_que: RedisSettings, user_id: int,
                           message: str):
    """
    Добавляет задачи в очередь
    :param redis_que:
    :param user_id:
    :param message:
    :return:
    """
    queue_logger.debug('Entry')
    queue = await create_pool(redis_que)
    await queue.enqueue_job(function='safe_send_message',
                            user_id=user_id,
                            message=message)
    queue_logger.debug('Exit')

async def mass_mailing(redis_que: RedisSettings, user_ids: set[int],
                       message: str, delay=0.1):
    """
    Массовая рассылка
    :param delay:
    :param redis_que:
    :param user_ids:
    :param message:
    :return:
    """
    queue_logger.debug('Entry')
    queue_logger.info(f"Рассылка началась для {len(user_ids)} юзеров")

    for user_id in user_ids:
        await add_mailing_task(user_id=user_id,
                               redis_que=redis_que,
                               message=message)
        await asyncio.sleep(delay)
    queue_logger.debug('Exit')

async def run_arq_worker(redis_que: RedisSettings, bot: Bot):
    async def startup(ctx):
        ctx['bot'] = bot  # Передаем бота в контекст

    worker = Worker(functions=[safe_send_message],
                    redis_settings=redis_que, on_startup=startup,
                    max_jobs=5, handle_signals=False,
                    health_check_interval=15)
    await worker.async_run()
