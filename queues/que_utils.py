import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import (TelegramRetryAfter,
                                TelegramBadRequest,
                                TelegramUnauthorizedError)
from arq import create_pool, Worker
from arq.connections import RedisSettings

from keyboards import kb_admin
from lexicon import LexiconRu

queue_logger = logging.getLogger(__name__)

async def safe_send_message(ctx: dict,
                            user_id: int,
                            message: str,
                            retries=3) -> bool:
    """
    Асинхронно отправляет сообщение с обработкой ошибок и повторными попытками.
    """
    queue_logger.debug('Entry')

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

    queue_logger.debug('Exit False')
    return False

async def mass_mailing(redis_que: RedisSettings, user_ids: set[int],
                       message: str, admin_ids: str, end_cert: str,  delay=0.1):
    """
    Массовая рассылка и отправка уведомления после завершения.
    :param admin_ids:
    :param end_cert:
    :param delay:
    :param redis_que:
    :param user_ids:
    :param message:
    :return:
    """
    queue_logger.debug('Entry')
    queue_logger.info(f"Рассылка началась для {len(user_ids)} юзеров")

    queue = await create_pool(redis_que)
    admins = set(map(int, admin_ids.split()))
    successful = 0
    fail = 0
    tasks = []
    for user_id in user_ids:
        job = await queue.enqueue_job(function='safe_send_message',
                               user_id=user_id,
                               message=message)
        tasks.append(job)
        await asyncio.sleep(delay)

    # Ожидание выполнения всех задач
    for task in tasks:
        try:
            result = await task.result()
            if result:
                successful += 1
        except Exception as e:
            fail += 1
            queue_logger.error(f"Ошибка при выполнении задачи: {e}")

    # Добавляем задачу уведомления в очередь после завершения
    # отправки всех сообщений
    await queue.enqueue_job(function='on_mailing_completed',
                            end_cert=end_cert, admins=admins,
                            counter_users=successful, fail=fail)

    queue_logger.debug('Exit')

async def on_mailing_completed(ctx: dict, end_cert: str, admins: set[int],
                               counter_users: int, fail: int):
    """
    Callback-функция для уведомления администратора после завершения рассылки.
    """
    queue_logger.debug("Entry")

    bot: Bot = ctx.get('bot')

    # Отправляем уведомление администратору
    for admin in admins:
        await bot.send_message(chat_id=admin,
                text=f"Произведена рассылка✅\n"
                     f"Удачных доставок: {counter_users}\n"
                     f"Не удачных доставок: {fail}\n\n"
                f"{LexiconRu.text_adm_panel.format(end_cert=end_cert)}",
                reply_markup=kb_admin)
        await asyncio.sleep(delay=0.2)

    queue_logger.debug("Exit")

async def run_arq_worker(redis_que: RedisSettings, bot: Bot):
    async def startup(ctx):
        ctx['bot'] = bot  # Передаем бота в контекст

    worker = Worker(functions=[safe_send_message,   on_mailing_completed],
                    redis_settings=redis_que, on_startup=startup, max_jobs=5,
                    handle_signals=False, health_check_interval=15)
    await worker.async_run()
