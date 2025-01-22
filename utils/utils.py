import asyncio
import logging
import os
from dataclasses import dataclass
from collections.abc import Mapping
import io

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import Color
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards import BUTT_COURSES

logger_utils = logging.getLogger(__name__)


async def get_certificate(
        state: FSMContext, w_text=False):
    logger_utils.debug(f'Entry')
    try:
        user_name = await state.get_value('full_name')
        number_str: str = await state.get_value('number')
        if not number_str:
            number_str = '000001'
            await state.update_data(number=number_str)
        number = str(int(number_str)+1).zfill(6)
        logger_utils.debug(f'{number=}')

        course = BUTT_COURSES[await state.get_value('course')]
        logger_utils.debug(f'{course=}')
        gender = await state.get_value('gender')
        logger_utils.debug(f'{gender=}')

        base_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..', 'static'))

        template_name = None

        if gender == 'female':
            match course:
                case 'Лучший по Python.Часть 1':
                    template_name = '1 часть жен.pdf'
                case 'Лучший по Python.Часть 2':
                    template_name = '2 часть жен.pdf'
        elif gender == 'male':
            match course:
                case 'Лучший по Python.Часть 1':
                    template_name = '1 часть муж.pdf'
                case 'Лучший по Python.Часть 2':
                    template_name = '2 часть муж.pdf'

        font_path = os.path.join(base_dir, 'Bitter-Regular.ttf')
        template_file = os.path.join(base_dir, template_name)
        output_file = os.path.join(base_dir, 'mod_cert.pdf')

        if not os.path.exists(font_path):
            raise FileNotFoundError(f"Файл шрифта не найден: {font_path}")

        # Регистрация внешнего шрифта
        pdfmetrics.registerFont(TTFont('BitterReg', font_path))

        light_gray = Color(230 / 255, 230 / 255, 230 / 255)
        watermark_text = 'TEST VERSION'
        # Открываем исходный PDF
        reader = PdfReader(template_file)

        # Создаем объект для записи нового PDF
        writer = PdfWriter()

        for page_num in range(len(reader.pages)):
            # Читаем страницу
            page = reader.pages[page_num]
            # Создаем временный буфер для добавления текста
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            font_size = 16

            if len(user_name) in (24, 25):
                font_size = 15
            elif len(user_name) in (26, 27):
                font_size = 14
            elif len(user_name) in (28, 29, 30):
                font_size = 13

            # Определяем ширину текста
            text_width = can.stringWidth(user_name, 'BitterReg', font_size)
            # Добавляем текст
            can.setFont('BitterReg', font_size)
            page_width = letter[0]  # Ширина страницы
            x_position = (page_width - text_width) / 2 + 155
            # Добавляем текст по центру
            can.drawString(x_position, 306, user_name)

            can.setFont('BitterReg', 21)
            can.setFillColor(light_gray)
            can.drawString(440, 373, number)

            if w_text:
                # Устанавливаем прозрачный цвет и шрифт
                can.setFillColor(Color(0.3, 0, 0, alpha=0.7))
                can.setFont('Helvetica', 50)
                # Поворачиваем текст (опционально) на 45 градусов
                can.rotate(45)
                # Добавляем водяной знак
                can.drawString(110, 60, watermark_text)  # Позиция текста

            # Закрываем холст и сохраняем его содержимое в пакет
            can.showPage()
            can.save()

            # Перемещаемся в начало буфера
            packet.seek(0)

            # Преобразуем буфер в PDF-объект
            new_pdf = PdfReader(packet)

            # Вставляем новую страницу поверх старой
            page.merge_page(new_pdf.pages[0])

            # Добавляем измененную страницу в выходной PDF
            writer.add_page(page)

        with open(output_file, 'wb') as fh:
            writer.write(fh)
    except Exception as err:
        logger_utils.error(f'{err=}', exc_info=True)
    else:
        return output_file


@dataclass
class MessageProcessor:
    """
    Class for managing and processing chat messages.

    _message (Message | CallbackQuery): The message or callback query object.
    _state (FSMContext): The finite state machine context.
    """
    _type_update: Message | CallbackQuery
    _state: FSMContext

    async def deletes_messages(
            self, msgs_for_del=False, msgs_remove_kb=False,
            msgs_for_reset=False) -> None:
        """
        Deleting messages from chat based on passed parameters.
        This method removes various types of messages from a chat.
        Messages are deleted only if the corresponding parameters
        are set to True.
        If no parameters are specified, the method does not perform any
        actions.
        :param msgs_for_reset: bool
        :param msgs_for_del: bool
        :param msgs_remove_kb: bool
        :return: None
        """
        logger_utils.debug(f'Entry')

        if isinstance(self._type_update, Message):
            chat_id = self._type_update.chat.id
        else:
            chat_id = self._type_update.message.chat.id

        kwargs: dict = {
                'msgs_for_del': msgs_for_del,
                'msgs_remove_kb': msgs_remove_kb,
                'msgs_for_reset': msgs_for_reset}

        keys = [key for key, val in kwargs.items() if val]
        logger_utils.debug(f'{keys=}')

        if keys:
            for key in keys:
                msgs_ids: list = dict(await self._state.get_data()).get(key, [])
                logger_utils.debug(f'Starting to delete messages…')

                for msg_id in set(msgs_ids):
                    try:
                        await self._type_update.bot.delete_message(
                                chat_id=chat_id, message_id=msg_id)
                    except Exception as err:
                        logger_utils.warning(
                                f'Failed to delete message with id {msg_id=}: '
                                f'{err=}')
                await self._state.update_data({key: []})

        logger_utils.debug('Exit')

    async def save_msg_id(
            self, value: Message | CallbackQuery, msgs_for_del=False,
            msgs_remove_kb=False, msgs_for_reset=False) -> None:
        """
        The writes_msg_id_to_storage method is intended for writing an identifier
        messages in the store depending on the values of the passed flags.
        It analyzes the method signature, determines the parameters with the set
        defaults to True, and then stores the message ID
        in the corresponding list in the object's state.
        After the recording process is completed, a success message is logged.
        completion of the operation.
        :param msgs_for_reset:
        :param value: Message | CallbackQuery
        :param msgs_for_del: bool
        :param msgs_remove_kb: bool
        :return: None
        """
        logger_utils.debug('Entry')

        flags: dict = {
                'msgs_for_del': msgs_for_del,
                'msgs_remove_kb': msgs_remove_kb,
                'msgs_for_reset': msgs_for_reset}

        for key, val in flags.items():
            logger_utils.debug('Start writing data to storage…')
            if val:
                data: list = dict(await self._state.get_data()).get(key, [])
                if value.message_id not in data:
                    data.append(str(value.message_id))
                    logger_utils.debug(f'Msg ID to recorded')
                logger_utils.debug('No msg ID to record')
                await self._state.update_data({key: data})
        logger_utils.debug('Exit')

    async def removes_inline_kb(self, key='msgs_remove_kb') -> None:
        """
        Removes built-in keyboards from messages.
        This function gets message IDs from the state and removes
        built-in keyboards from these messages. After removing the keyboards,
        the state is updated to clear the list of message IDs.
        Logs:
            — Start the keyboard removal process.
            — Errors when removing the keyboard.
            — Successful completion of the keyboard removal process.
        :param key: Str
        :return: None
        """
        logger_utils.debug('Entry')

        msgs: list = dict(await self._state.get_data()).get(key, [])

        if isinstance(self._type_update, Message):
            chat_id = self._type_update.chat.id
        else:
            chat_id = self._type_update.message.chat.id

        for msg_id in set(msgs):
            try:
                await self._type_update.bot.edit_message_reply_markup(
                        chat_id=chat_id, message_id=msg_id)
            except TelegramBadRequest as err:
                logger_utils.error(f'{err}', stack_info=True)
        logger_utils.debug('Keyboard removed')
        await self._state.update_data({key: []})

        logger_utils.debug('Exit')

    async def change_message(self, key='msg_id_for_change') -> None:
        pass

    async def delete_message(self, key='msg_id_for_del') -> None:
        """
        Deletes a message using the specified key. The method retrieves data from
        states and uses them to delete a message with the specified key.
        Args: key (str): The key by which the message will be found for
        removal. Default 'msg_id_for_change'. Return: None.
        :param key: str
        :return: None
        """
        logger_utils.debug('Entry')
        data = await self._state.get_data()
        chat_id = self._type_update.message.chat.id
        await self._type_update.bot.delete_message(chat_id=chat_id,
                                                   message_id=data.get(key))
        logger_utils.debug('Exit')

    @staticmethod
    async def deletes_msg_a_delay(value: Message, delay: int) -> None:
        """
         Deletes a message after a specified time interval.
         Arguments: message (types.Message): The message to be deleted.
                    delay (int): Time in seconds before the message is deleted.
                    Returns: None
        :param value: Message
        :param delay: int
        :return: None
        """
        await asyncio.sleep(delay)
        await value.delete()


class ImmutableDict(Mapping):
    def __init__(self, data=None):
        if data is None:
            self._data = {}
        else:
            self._data = dict(data)

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return f'ImmutableDict({self._data})'

    def __call__(self, key):
        return self._data[key]


async def get_immutable_dict(*args):
    temp_dict = {}
    for dct in args:
        temp_dict.update(dct)
    return ImmutableDict(temp_dict)
