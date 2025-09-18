import logging
import re
from datetime import datetime, timedelta

from aiogram.enums import ContentType
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from utils import get_username
from utils.utils import MessageProcessor

logger_filters = logging.getLogger(__name__)


class IsValidProfileLink(BaseFilter):
    """
    Проверяет, содержит ли сообщение валидную ссылку на профиль,
    где цифры в URL это ID пользователя. Поддерживает:
    1. Ссылки внутри текста с пробелами/переносами
    2. Форматы:
       - https://stepik.org/users/USER_ID
       - https://stepik.org/users/USER_ID/profile
       - https://stepik.org/users/USER_ID/
    """
    async def __call__(self, msg: Message, state: FSMContext) -> bool | dict[str, str]:
        msg_processor = MessageProcessor(msg, state)
        text = msg.text.strip()

        # Ищет ссылку в любом месте текста
        match = re.search(r'\bhttps?://[^\s/]+/users/(\d+)(?:/profile)?/?\b',
                text, re.IGNORECASE)

        if match:
            stepik_user_id = match.group(1)
            return {'stepik_user_id': stepik_user_id}

        await msg.delete()
        logger_filters.warning(f'Ссылка не корректна:{msg.from_user.id}'
                              f':{await get_username(msg)}:{msg.text}')
        value = await msg.answer(
                f'{await get_username(msg)}, ваша ссылка на профиль не корректна, '
                f'попробуйте еще раз.')
        await msg_processor.deletes_msg_a_delay(value, delay=6, indication=True)
        return False


class IsAdmins(BaseFilter):
    async def __call__(self, msg: Message, admins: str) -> bool:
        logger_filters.debug('Entry')

        user_id = str(msg.from_user.id)
        admins_id = admins.split()
        logger_filters.debug(f'{admins_id=}')

        logger_filters.debug('Exit')
        return user_id in admins_id


class IsFullName(BaseFilter):
    async def __call__(self, msg: Message, state: FSMContext) -> bool | dict:
        logger_filters.debug(f'Entry {__class__.__name__}')
        msg_processor = MessageProcessor(msg, state)

        # - Разрешает дефисы в словах (но не в начале/конце)
        # - Разрешает пробел между словами
        pattern = r'''
            ^
            [ёа-яa-z]+(?:-[ёа-яa-z]+)?  # Первое слово (с возможным дефисом)
            (?:\s+[ёа-яa-z]+(?:-[ёа-яa-z]+)?)+  # Остальные слова
            $
        '''

        if msg.content_type != ContentType.TEXT:
            await self._delete_and_notify(msg, msg_processor)
            return False

        text = msg.text.strip()
        words = text.split()

        # Проверяем количество слов (минимум 2)
        if len(words) < 2:
            logger_filters.warning(f'Не корректные ФИО:{msg.from_user.id}:'
                                   f'{await get_username(msg)}:'
                                   f'{msg.text}')
            await self._delete_and_notify(msg, msg_processor,
                    message="Введите хотя бы два слова: Имя и Фамилию 😉")
            return False

        # Проверяем регулярное выражение и отсутствие цифр
        if (re.fullmatch(pattern, text,
                         flags=re.VERBOSE | re.IGNORECASE) and not any(
                char.isdigit() for char in text)):
            # Капитализируем каждую часть слов с дефисами
            capitalized_words = [
                    "-".join(part.capitalize() for part in word.split("-")) for
                    word in words]
            logger_filters.debug(f'Exit {__class__.__name__}')
            return {'full_name': ' '.join(capitalized_words)}
        else:
            logger_filters.warning(f'Не корректные ФИО:{msg.from_user.id}:'
                                   f'{await get_username(msg)}:'
                                   f'{msg.text}')
            await self._delete_and_notify(msg, msg_processor,
                    message="Некорректно введены данные")
            return False

    @staticmethod
    async def _delete_and_notify(msg, msg_processor, message: str = None):
        """Удаляет сообщение и отправляет уведомление"""
        await msg.bot.delete_message(chat_id=msg.chat.id,
                                     message_id=msg.message_id)
        if message:
            response = await msg.answer(f"{await get_username(msg)}, {message}")
            await msg_processor.deletes_msg_a_delay(response, delay=7,
                                                    indication=True)


class IsCorrectData(BaseFilter):
    async def __call__(self,
                       msg: Message,
                       state: FSMContext,
                       msg_processor: MessageProcessor) -> bool | dict[str, str]:
        logger_filters.debug(f'Entry {__class__.__name__}')
        username = await get_username(msg)
        
        if msg.content_type != ContentType.TEXT:
            await msg.bot.delete_message(
                chat_id=msg.chat.id,
                message_id=msg.message_id)
            return False
        
        if not msg.text:
            logger_filters.debug(f'Exit False {__class__.__name__}')
            await msg.bot.delete_message(
                chat_id=msg.chat.id,
                message_id=msg.message_id)
            return False
        
        start_kurse = datetime.strptime('01.03.2024', "%d.%m.%Y")
        date_str = msg.text.strip()
        logger_filters.debug(f'{date_str=}')
        
        try:
            date_obj = datetime.strptime(date_str, "%d.%m.%Y")
            if date_obj.date() < start_kurse.date():
                await msg.bot.delete_message(
                    chat_id=msg.chat.id, message_id=msg.message_id)
                value = await msg.answer(
                    f'{username}, вы указали дату, когда курс еще не был '
                    f'создан)')
                await msg_processor.deletes_msg_a_delay(
                    value,
                    delay=6,
                    indication=True)
                return False
            
            server_date = datetime.now().date()
            if date_obj.date() > (server_date + timedelta(days=1)):
                await msg.bot.delete_message(
                    chat_id=msg.chat.id, message_id=msg.message_id)
                value = await msg.answer(
                    f'{username}, вы указали дату из будущего.\n'
                    f'Пожалуйста, повторите.')
                await msg_processor.deletes_msg_a_delay(
                    value,
                    delay=6,
                    indication=True)
                return False
            
            logger_filters.debug(f'Exit Done {__class__.__name__}')
            return {'date': date_str}
        
        except ValueError:
            logger_filters.warning(
                f'Некорректная дата:{username}:'
                f'{msg.from_user.id}:[{date_str}]')
            logger_filters.debug(f'Exit False {__class__.__name__}')
            await msg.bot.delete_message(
                chat_id=msg.chat.id,
                message_id=msg.message_id)
            value = await msg.answer(
                'Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ')
            await msg_processor.deletes_msg_a_delay(value, 5, indication=True)
            return False

class IsCorrectEmail(BaseFilter):
    async def __call__(self, msg: Message) -> bool:
        """
        Проверяет валидность email по регулярному выражению.
        Покрывает большинство повседневных случаев, но не проверяет
        существование домена.
        :param msg: Message
        :return: bool
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
