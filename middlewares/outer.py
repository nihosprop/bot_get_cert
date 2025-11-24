import asyncio
import logging
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict

from aiogram.dispatcher.event.bases import CancelHandler
from redis.asyncio import Redis

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import (CallbackQuery, Message, TelegramObject, User, Update)

from utils import get_username
from utils.utils import MessageProcessor
from lexicon.lexicon_ru import LexiconRu

logger_middl_outer = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).parent.parent


class RedisMiddleware(BaseMiddleware):
    """
    Передает Redis клиент в контекст, для доступа в хэндлерах
    """

    def __init__(self, redis):
        self.redis_data = redis

    async def __call__(self, handler, event, data):
        data['redis_data'] = self.redis_data
        return await handler(event, data)


class ThrottlingMiddleware(BaseMiddleware):
    """A middleware for limiting the frequency of requests from a single user.
    Uses Redis to store information about request frequency. If the frequency
    exceeds the set threshold, requests are blocked.
    Attributes:
        storage (RedisStorage): An object for interacting with Redis.
        ttl (int | None): The time-to-live for the key in milliseconds. If
        None, rate limiting is disabled. """

    def __init__(self, storage: RedisStorage, ttl: int | None = None):
        """
        Initializes the middleware for limiting the frequency of requests.
        Args: storage (RedisStorage): An object for interacting with Redis.
        ttl (int | None, optional): The time-to-live for the key in
        milliseconds. If None, rate limiting is disabled.
        :param storage: RedisStorage.
        :param ttl:
        """
        self.storage = storage
        self.ttl = ttl

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]) -> Any:
        """Handles an event and applies the frequency limitation. If rate
        limiting is enabled and the user has exceeded the allowed frequency,
        the event is ignored, and the user receives an appropriate
        notification. Args: handler (Callable): The next handler in the chain.
        event (TelegramObject): The current event. data (Dict[str, Any]):
        Additional data. Returns: Any: The result of calling the next handler.
        """
        logger_middl_outer.debug(f'Entry {__class__.__name__}')
        # Проверяем тип чата
        if hasattr(event, 'chat') and event.chat.type in [
                ChatType.GROUP,
                ChatType.SUPERGROUP]:
            logger_middl_outer.debug(f'Exit')
            # Если это групповой чат, пропускаем тротлинг
            return await handler(event, data)

        admins_id = data.get('admins').split()
        if str(event.from_user.id) in admins_id:
            logger_middl_outer.debug(f'Exit')
            return await handler(event, data)

        state: FSMContext = data.get('state')
        msg_processor = MessageProcessor(event, state)

        if self.ttl is None:
            logger_middl_outer.debug(f'Exit')
            return await handler(event, data)

        user: User = data.get('event_from_user')
        throttl_user_id = f'throttl_{user.id}'
        check_user = await self.storage.redis.get(name=throttl_user_id)

        if check_user and int(check_user.decode()) == 1:

            if isinstance(event, Message):
                value = await event.answer(text=LexiconRu.text_antispam)
                asyncio.create_task(msg_processor.deletes_msg_a_delay(value, 5))

            if isinstance(event, CallbackQuery):
                await event.answer()

            asyncio.create_task(
                msg_processor.deletes_msg_a_delay(event, 6, indication=True))
            await self.storage.redis.set(name=throttl_user_id, value=2, px=5000)

            logger_middl_outer.warning(
                f'Throttling:{await get_username(event)}:{throttl_user_id}')
            logger_middl_outer.debug(f'Exit {__class__.__name__}')
            return

        elif check_user and int(check_user.decode()) == 2:
            asyncio.create_task(msg_processor.deletes_msg_a_delay(event, 5))
            logger_middl_outer.debug(f'Exit')
            return

        if not check_user:
            await self.storage.redis.set(name=throttl_user_id, value=1,
                                         px=self.ttl)

        logger_middl_outer.debug(f'Exit {__class__.__name__}')
        
        return await handler(event, data)


class MsgProcMiddleware(BaseMiddleware):
    """
    Middleware для обработки Message и callback-запросов.
    Добавляет экземпляр класса MessageProcessor в контекст(в данные (data)),
    который
    может
    быть использован в обработчиках для дополнительной обработки сообщений.
    Attrs: None
    """
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]) -> Any:
        """
        Обрабатывает event(входящее событие).
        Args:
            handler: Обработчик, который будет вызван после middleware.
            event: Входящее событие (Message или CallbackQuery).
            data: Словарь с данными, которые передаются между middleware и обработчиками.
        Returns:
            handler.
        """
        processor = MessageProcessor(event, _state=data["state"])
        data["msg_processor"] = processor
        return await handler(event, data)


logger = logging.getLogger(__name__)


class StrictMaintenanceMiddleware(BaseMiddleware):
    """
    Строгая заглушка на технические работы.
    Блокирует абсолютно все события для всех пользователей, кроме админов.
    """
    
    def __init__(self,
                 redis: Redis,
                 enabled: bool = False,
                 message: str = "⚙️ Идут технические работы. Пожалуйста, попробуйте позже."):
        self.redis = redis
        self.enabled = enabled
        self.message = message
    
    async def __call__(self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]) -> Any:
        # Логируем входящее событие
        logger.info(
            f"Processing event: {event.update_id}, type: {event.event_type}")
        
        # Получаем список админов
        admins = data.get("admins", [])
        if isinstance(admins, str):
            admins = admins.split()
        
        user = data.get("event_from_user")
        user_id = str(user.id) if user else None
        
        if user_id and user_id in admins:
            return await handler(event, data)
        if hasattr(event, 'event') and hasattr(event.event, 'from_user'):
            user_id = event.event.from_user.id
        elif hasattr(
            event,
            'message') and event.message and event.message.from_user:
            user_id = event.message.from_user.id
        elif hasattr(event, 'callback_query') and event.callback_query:
            user_id = event.callback_query.from_user.id
        elif hasattr(event, 'query') and event.query:
            user_id = event.query.from_user.id
        
        # Пропускаем только админов
        if user_id and str(user_id) in admins:
            logger.info(f"Allowing event for admin: {user_id}")
            return await handler(event, data)
        
        # Проверяем статус техработ
        try:
            redis_flag = await self.redis.get("maintenance")
            if isinstance(redis_flag, bytes):
                redis_flag = redis_flag.decode()
            is_maintenance = self.enabled or (redis_flag == "1")
            logger.info(f"Maintenance status: {is_maintenance}")
        except Exception as e:
            logger.error(f"Redis error: {e}")
            is_maintenance = self.enabled
        
        if not is_maintenance:
            return await handler(event, data)
        
        # Блокируем событие
        logger.info(f"Blocking event during maintenance: {event.update_id}")
        
        # Отправляем уведомление в зависимости от типа события
        try:
            if getattr(event, "message", None):
                await event.message.answer(self.message)
            elif getattr(event, "callback_query", None):
                await event.callback_query.answer(self.message, show_alert=True)
            else:
                # универсальный fallback для прочих апдейтов (inline, shipping и т.д.)
                bot = data.get("bot")
                user = data.get("event_from_user")
                if bot and user:
                    await bot.send_message(chat_id=user.id, text=self.message)
        except Exception as e:
            logger.error(f"Failed to send maintenance message: {e}")
        
        # Полностью останавливаем обработку события
        raise CancelHandler()

 
