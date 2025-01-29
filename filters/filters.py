import logging
import re
from datetime import datetime

from aiogram.enums import ContentType
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from utils.utils import MessageProcessor

logger_filters = logging.getLogger(__name__)


class StateGroupFilter(BaseFilter):
    """
    Фильтр для проверки, принадлежит ли текущее состояние пользователя
    к указанной группе состояний (StatesGroup).
    Можно использовать на уровне роутера, чтобы автоматически
    фильтровать апдэйты по всем состояниям, принадлежащим определенной группе.
    Атрибуты:
        state_group (StatesGroup): Группа состояний (например, FSMPromoCode),
                                      к которой будет применяться фильтр.
    Пример использования для фильтрации на уровне роутеров:
        router.message.filter(StateGroupFilter(FSMPromoCode))
        router.callback_query.filter(StateGroupFilter(FSMPromoCode))
    """

    def __init__(self, state_group):
        self.state_group = state_group

    async def __call__(
            self, event: Message | CallbackQuery, state: FSMContext) -> bool:
        current_state = await state.get_state()
        return current_state in [state.state for state in
                self.state_group.__states__.values()]


class IsValidProfileLink(BaseFilter):
    """
    Проверяет, является ли валидной ссылкой на профиль,
    где цифры в URL это ID пользователя.
    Поддерживает два формата ссылок:
    1. https://stepik.org/users/USER_ID/profile
    2. https://stepik.org/users/USER_ID
    """

    async def __call__(self, msg: Message, state: FSMContext) -> bool | dict[
        str, str]:
        msg_processor = MessageProcessor(msg, state)
        link = msg.text
        match = re.match(r'^https?://[^/]+/users/(\d+)(?:/profile)?$', link)
        if match:
            stepik_user_id: str = match.group(1)
            return {'stepik_user_id': stepik_user_id}
        await msg.delete()
        value = await msg.answer(f'{msg.from_user.first_name}, ваша ссылка на '
                                 f'профиль не корректна, попробуйте еще раз.')
        await msg_processor.deletes_msg_a_delay(value, delay=6, indication=True)
        return False


class IsAdmins(BaseFilter):
    async def __call__(self, msg: Message, admins: str) -> bool:
        logger_filters.debug('Entry')

        user_id = str(msg.from_user.id)
        admins_id = admins.split()

        logger_filters.debug(f'{admins_id}')
        logger_filters.debug('Exit')
        return user_id in admins_id


class IsFullName(BaseFilter):
    async def __call__(self, msg: Message, state: FSMContext) -> bool | dict:
        logger_filters.debug(f'Entry {__class__.__name__}')
        msg_processor = MessageProcessor(msg, state)
        pattern = r'^[ёа-яa-z]+(?: [ёа-яa-z]+)+$'

        if msg.content_type != ContentType.TEXT:
            await msg.bot.delete_message(chat_id=msg.chat.id,
                                         message_id=msg.message_id)
            value = await msg.answer(f'{msg.from_user.first_name}, '
                                     f'введите пожалуйста Имя и Фамилию текстом '
                                     f';)')
            await msg_processor.deletes_msg_a_delay(value, delay=6,
                                                    indication=True)

        # Проверка на количество слов
        words = msg.text.split()
        if len(words) < 2:
            await msg.bot.delete_message(chat_id=msg.chat.id,
                                         message_id=msg.message_id)
            value = await msg.answer(f'{msg.from_user.first_name}, '
                                     f'Введите хотя бы два слова: Имя и '
                                     f'Фамилию ;)')
            await msg_processor.deletes_msg_a_delay(value, delay=7,
                                                    indication=True)
            return False

        # Проверка на соответствие регулярному выражению и отсутствие цифр
        if re.match(pattern, msg.text.lower()) and not any(
                    char.isdigit() for char in msg.text):
            logger_filters.debug(f'Exit True {__class__.__name__}')
            return {'full_name': ' '.join(word.capitalize() for word in words)}
        else:
            await msg.bot.delete_message(chat_id=msg.chat.id,
                                        message_id=msg.message_id)
            value = await msg.answer(f'{msg.from_user.first_name}, '
                            f'Некорректно введены данные')
            await msg_processor.deletes_msg_a_delay(value, delay=7,
                                                    indication=True)

            logger_filters.debug(f'Exit False {__class__.__name__}')
            return False


class IsCorrectData(BaseFilter):
    async def __call__(self, msg: Message, state: FSMContext) -> bool | dict[
        str, str]:
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
                                         f'дату, когда курс еще не '
                                         f'существовал🙃\n'
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
            value = await msg.answer('Дата не корректна.\n'
                                     'Будьте внимательны при вводе🧐')
            await msg_processor.deletes_msg_a_delay(value, 5, indication=True)
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
