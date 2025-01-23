import logging
import re
from datetime import datetime

from aiogram.enums import ContentType
from aiogram.filters import BaseFilter
from aiogram.types import Message

from utils import MessageProcessor

logger_filters = logging.getLogger(__name__)


class IsValidProfileLink(BaseFilter):
    """
    Проверяет, является ли валидной ссылкой на профиль,
    где цифры в URL это ID пользователя.
    """
    async def __call__(self, msg: Message) -> bool | dict[str, str]:
        link = msg.text
        pattern = r'^https?://[^/]+/users/(\d+)/profile$'
        match = re.match(pattern, link)
        if bool(match):
            stepik_user_id = link.split('/')[-2]
            return {'stepik_user_id': stepik_user_id}
        return False


class IsAdmin(BaseFilter):
    async def __call__(self, msg: Message, superadmin) -> bool:
        logger_filters.debug('Entry')
        user_id = str(msg.from_user.id)
        logger_filters.debug(f'In {__class__.__name__}:{user_id=}'
                             f':{superadmin=}\n{user_id == superadmin=}')
        logger_filters.debug('Exit')
        return user_id == superadmin


class IsFullName(BaseFilter):
    async def __call__(self, msg: Message) -> bool:
        logger_filters.debug(f'Entry {__class__.__name__}')
        pattern = r'^[А-ЯA-Z][а-яa-z]+ [А-ЯA-Z][а-яa-z]+$'

        if msg.content_type != ContentType.TEXT:
            await msg.bot.delete_message(chat_id=msg.chat.id,
                                         message_id=msg.message_id)

        if re.match(pattern, msg.text):
            logger_filters.debug(f'Exit True {__class__.__name__}')
            return True
        else:
            logger_filters.debug(f'Exit False {__class__.__name__}')
            await msg.bot.delete_message(chat_id=msg.chat.id,
                                         message_id=msg.message_id)
            return False


class IsCorrectData(BaseFilter):
    async def __call__(self, msg: Message) -> bool | dict[str, str]:
        logger_filters.debug(f'Entry {__class__.__name__}')

        if msg.content_type != ContentType.TEXT:
            await msg.bot.delete_message(chat_id=msg.chat.id,
                                         message_id=msg.message_id)

        if not msg.text:
            logger_filters.debug(f'Exit False {__class__.__name__}')
            await msg.bot.delete_message(chat_id=msg.chat.id,
                                         message_id=msg.message_id)
            return False

        start_kurse = datetime.strptime('01.03.2024', "%d.%m.%Y")
        date_str = msg.text
        logger_filters.debug(f'{date_str=}')

        try:
            date_obj = datetime.strptime(date_str, "%d.%m.%Y")

            if date_obj.date() < start_kurse.date():
                await msg.bot.delete_message(chat_id=msg.chat.id,
                                             message_id=msg.message_id)
                return False

            if date_obj.date() > datetime.now().date():
                await msg.bot.delete_message(chat_id=msg.chat.id,
                                             message_id=msg.message_id)
                raise ValueError
            logger_filters.debug(f'Exit Done {__class__.__name__}')
            return {'date': date_str}

        except ValueError as err:
            logger_filters.warning(f'Некорректная дата: {err}')
            logger_filters.debug(f'Exit False {__class__.__name__}')
            await msg.bot.delete_message(chat_id=msg.chat.id,
                                         message_id=msg.message_id)
            return False


class IsCorrectEmail(BaseFilter):
    async def __call__(self, msg: Message):
        """
        Проверяет валидность email по регулярному выражению.
        Покрывает большинство повседневных случаев, но не проверяет
        существование домена.
        """
        if msg.content_type != ContentType.TEXT:
            await msg.bot.delete_message(chat_id=msg.chat.id,
                                         message_id=msg.message_id)
        email = msg.text.strip()
        pattern = r'''
                ^
                [a-zA-Z0-9_.+-]+    # Локальная часть (до @)
                @
                [a-zA-Z0-9-]+       # Домен
                (\.[a-zA-Z0-9-]+)*  # Поддомены
                \.[a-zA-Z]{2,}      # Верхнеуровневый домен (минимум 2 буквы)
                $
            '''
        if re.fullmatch(pattern, email, re.VERBOSE):
            return True
        else:
            await msg.bot.delete_message(chat_id=msg.chat.id,
                                         message_id=msg.message_id)
            return False

