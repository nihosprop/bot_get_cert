import asyncio
import logging
import os
from dataclasses import dataclass
import io

from concurrent.futures import ThreadPoolExecutor
from PyPDF2 import PdfReader, PdfWriter
from aiogram.client.session import aiohttp
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import Color
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from redis.asyncio import Redis

from keyboards import BUTT_COURSES

logger_utils = logging.getLogger(__name__)

# Создаем пул потоков для выполнения синхронных операций
executor = ThreadPoolExecutor(max_workers=4)

async def get_stepik_access_token(
        client_id, client_secret, redis_client: Redis) -> str:
    """
    Получает токен доступа для Stepik API.
    :param redis_client: 
    :param client_id: Идентификатор клиента.
    :param client_secret: Секретный ключ клиента.
    :return: Токен доступа
    :raises: RuntimeError, если не удалось получить токен.
    """
    cached_token = await redis_client.get('stepik_token')
    url = 'https://stepik.org/oauth2/token/'

    if cached_token:
        logger_utils.debug("Используется кэшированный токен из Redis.")
        return cached_token.decode('utf-8')

    data = {
            'grant_type': 'client_credentials',
            'client_id': f'{client_id}',
            'client_secret': f'{client_secret}'}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as resp:
                if resp.status != 200:
                    error_message = await resp.text()
                    logger_utils.error(f"Ошибка при запросе токена: "
                                       f"{error_message}", exc_info=True)
                    raise RuntimeError(
                        f"Не удалось получить токен: {error_message}")
                response = await resp.json()
                access_token = response.get('access_token')
                if not access_token:
                    raise RuntimeError("Токен не найден в ответе API.")
                # Сохраняем токен в Redis с TTL
                await redis_client.set('stepik_token', access_token, ex=3600)
                logger_utils.debug("Токен успешно получен и сохранён в Redis.")
                return access_token

    except aiohttp.ClientError as err:
        logger_utils.error(f"Ошибка сети при запросе токена: {err}",
                           exc_info=True)
        raise RuntimeError(f"Ошибка сети: {err}")

    except Exception as err:
        logger_utils.error(f"Неожиданная ошибка при запросе токена: {err}",
                           exc_info=True)
        raise RuntimeError(f"Неожиданная ошибка: {err}")


async def check_certificate(stepik_user_id, course_id, access_token):
    page_number = 1
    while True:
        try:
            api_url = (f'https://stepik.org/api/certificates?user='
                       f'{stepik_user_id}&page={page_number}')
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers={
                        'Authorization': 'Bearer ' + access_token}) as response:
                    if response.status == 429:
                        logger_utils.warning(
                                'Превышен лимит запросов. Ожидание…')
                        await asyncio.sleep(10)
                    response.raise_for_status()
                    data = await response.json()

                    # Проверяем сертификаты на текущей странице
                    for certificate in data['certificates']:
                        # logger_utils.debug(f'{certificate}')
                        if certificate['course'] == int(course_id):
                            return True  # Сертификат за курс найден

                    # Если есть следующая страница, переходим к ней
                    if data['meta']['has_next']:
                        page_number += 1
                        await asyncio.sleep(1)  # Задержка между запросами
                    else:
                        break  # Больше страниц нет
        except Exception as err:
            logger_utils.error(f"Ошибка при запросе сертификатов: {err}",
                               exc_info=True)
            raise
    return False  # Сертификат за курс не найден


def sync_generate_certificate(
        state_data, w_text=False):
    """
    Синхронная функция для генерации сертификата.
    """
    logger_utils.debug(f'Entry')
    try:
        user_name = state_data.get('full_name')
        number = state_data.get('number')
        course = BUTT_COURSES[state_data['course']]
        gender = state_data.get('gender')

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
        output_file = os.path.join(base_dir, f'BestInPython_№{number}.pdf')

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
            # Добавляем текст ФИО по центру
            can.drawString(x_position, 306, user_name)
            # Добавляем текст № сертификата
            can.setFont('BitterReg', 21)
            can.setFillColor(light_gray)
            can.drawString(440, 373, number)

            # Добавить водяной знак
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


async def generate_certificate(state: FSMContext, w_text=False):
    """
    Асинхронная обёртка для генерации сертификата.
    """
    logger_utils.debug('Entry')
    try:
        # Получаем данные из состояния
        state_data = await state.get_data()
        # Выполняем синхронную операцию в отдельном потоке
        output_file = await asyncio.to_thread(sync_generate_certificate, state_data, w_text)
        return output_file
    except Exception as err:
        logger_utils.error(f'{err=}', exc_info=True)
        raise


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
        Удаляет сообщение, используя указанный ключ. Метод извлекает данные из
        состояния и использует их для удаления сообщения с указанным ключом.
        Args: key (str): Ключ, по которому будет найдено сообщение
        удаление. По умолчанию «msg_id_for_change». Возвращает: None.
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
                    returns: None
        :param value: Message
        :param delay: int
        :return: None
        """
        await asyncio.sleep(delay)
        await value.delete()
