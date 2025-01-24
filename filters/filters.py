import logging
import re
from datetime import datetime

from aiogram.enums import ContentType
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from utils.utils import MessageProcessor

logger_filters = logging.getLogger(__name__)


class IsValidProfileLink(BaseFilter):
    """
    Проверяет, является ли валидной ссылкой на профиль,
    где цифры в URL это ID пользователя.
    Поддерживает два формата ссылок:
    1. https://stepik.org/users/USER_ID/profile
    2. https://stepik.org/users/USER_ID
    """
    async def __call__(self, msg: Message, state: FSMContext) -> bool | dict[str, str]:
        msg_processor = MessageProcessor(msg, state)
        link = msg.text
        match = re.match(r'^https?://[^/]+/users/(\d+)(?:/profile)?$', link)
        if match:
            stepik_user_id: str = match.group(1)
            return {'stepik_user_id': stepik_user_id}
        value = await msg.answer(f'{msg.from_user.first_name}, ваша ссылка на '
                                 f'профиль не корректна, попробуйте еще раз.')
        await msg_processor.deletes_msg_a_delay(value, delay=6, indication=True)
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
    async def __call__(self, msg: Message, state: FSMContext) -> bool:
        logger_filters.debug(f'Entry {__class__.__name__}')
        msg_processor = MessageProcessor(msg, state)
        pattern = r'^[А-ЯA-Z][а-яa-z]+ [А-ЯA-Z][а-яa-z]+$'

        if msg.content_type != ContentType.TEXT:
            await msg.bot.delete_message(chat_id=msg.chat.id,
                                         message_id=msg.message_id)
            value = await msg.answer(f'{msg.from_user.first_name}, '
                                     f'введите пожалуйста Имя и Фамилию текстом '
                                     f';)')
            await msg_processor.deletes_msg_a_delay(value, delay=6,
                                                    indication=True)

        if re.match(pattern, msg.text):
            logger_filters.debug(f'Exit True {__class__.__name__}')
            return True
        else:
            logger_filters.debug(f'Exit False {__class__.__name__}')
            await msg.bot.delete_message(chat_id=msg.chat.id,
                                         message_id=msg.message_id)
            value = await msg.answer(f'{msg.from_user.first_name}, '
                                     f'Вы ввели Имя и Фамилию в некорректном '
                                     f'формате.\n'
                                     f'Посмотрите на пример выше ;)')
            await msg_processor.deletes_msg_a_delay(value,
                                                    delay=7, indication=True)
            return False


class IsCorrectData(BaseFilter):
    async def __call__(self, msg: Message, state: FSMContext) -> bool | dict[str, str]:
        logger_filters.debug(f'Entry {__class__.__name__}')
        msg_processor = MessageProcessor(msg, state)

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
                value = await msg.answer(f'{msg.from_user.first_name}, '
                                       f'вы прислали '
                                 f'дату, когда курс еще не существовал🙃\n'
                                 f'Повнимательнее пожалуйста.')
                await msg_processor.deletes_msg_a_delay(value, delay=6,
                                                        indication=True)
                return False

            if date_obj.date() > datetime.now().date():
                await msg.bot.delete_message(chat_id=msg.chat.id,
                                             message_id=msg.message_id)
                value = await msg.answer(f'{msg.from_user.first_name},'
                                         f' ваша дата из будущего😄\n'
                                         f'Повнимательнее пожалуйста.')
                await msg_processor.deletes_msg_a_delay(value, delay=6,
                                                        indication=True)
                raise ValueError
            logger_filters.debug(f'Exit Done {__class__.__name__}')
            return {'date': date_str}

        except ValueError as err:
            logger_filters.warning(f'Некорректная дата: {err=}')
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
