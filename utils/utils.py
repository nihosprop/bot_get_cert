import asyncio
import logging
import os
from dataclasses import dataclass
import io

from datetime import datetime, timedelta
from PyPDF2 import PdfReader, PdfWriter
from aiogram.client.session import aiohttp
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import Color
from aiogram.methods.get_chat_member import GetChatMember
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message, LinkPreviewOptions
from redis.asyncio import Redis

from keyboards import BUTT_COURSES

logger_utils = logging.getLogger(__name__)

# Создаем пул потоков для выполнения синхронных операций
# executor = ThreadPoolExecutor(max_workers=4)

async def check_user_in_group(_type_update: Message | CallbackQuery) -> bool:
    target_chat = '@best_python1/1'
    user_id = _type_update.from_user.id
    try:
        chat_member = await _type_update.bot.get_chat_member(target_chat, user_id)
        status = chat_member.status in {'member', 'administrator', 'creator'}
        logger_utils.debug(f'Проверка человека в чате {status}')
    except TelegramBadRequest:
        return False
    else:
        return status

async def get_username(_type_update: Message | CallbackQuery) -> str:
    """
       Возвращает имя пользователя.
       Если first_name отсутствует, использует username.
       Если username также отсутствует, возвращает "Аноним".

       :param _type_update: Объект Message или CallbackQuery.
       :return: Имя пользователя.
       """
    user_name = _type_update.from_user.first_name

    if not user_name:
        if username := _type_update.from_user.username:
            return f'@{username}'
        else:
            return str(_type_update.from_user.id)
    return user_name

@dataclass
class StepikService:
    client_id: str
    client_secret: str
    redis_client: Redis

    async def get_stepik_access_token(self) -> str:
        """
        Получает токен доступа для Stepik API.
        :return str: Токен доступа
        :raises: RuntimeError, если не удалось получить токен.
        """
        cached_token = await self.redis_client.get('stepik_token')
        url = 'https://stepik.org/oauth2/token/'

        if cached_token:
            logger_utils.debug("Используется кэшированный токен из Redis.")
            return cached_token

        data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret}

        try:
            async with (aiohttp.ClientSession() as session):
                async with session.post(url,
                                        data=data,
                                        allow_redirects=True) as resp:
                    if resp.status != 200:
                        error_message = await resp.text()
                        logger_utils.error(
                            f"Ошибка при запросе токена: {error_message}",
                            exc_info=True)
                        raise RuntimeError(
                            f"Не удалось получить токен: {error_message}")
                    response = await resp.json()
                    access_token = response.get('access_token')
                    if not access_token:
                        raise RuntimeError("Токен не найден в ответе API.")
                    # Сохраняем токен в Redis с TTL
                    await self.redis_client.set('stepik_token', access_token,
                                                ex=3600)
                    logger_utils.debug(
                        "Токен успешно получен и сохранён в Redis.")
                    return access_token

        except aiohttp.ClientError as err:
            logger_utils.error(f"Ошибка сети при запросе токена: {err}",
                               exc_info=True)
            raise RuntimeError(f"Ошибка сети: {err}")

        except Exception as err:
            logger_utils.error(f"Неожиданная ошибка при запросе токена: {err}",
                               exc_info=True)
            raise RuntimeError(f"Неожиданная ошибка: {err}")

    async def check_cert_in_user(self, tg_user_id: str, course_id: str) \
            -> bool | str:
        """
        Проверяет, есть ли номер сертификата у пользователя.
        :param course_id:
        :param tg_user_id: ID пользователя.
        :return: True и номер сертификата, если найден, иначе False.
        """
        certificate = await self.redis_client.hget(f'{tg_user_id}',
                                                   f'{course_id}')
        return certificate if certificate else False

    async def save_certificate_number(self, user_id: str, course_id: str):
        """
        Сохраняет номер сертификата в Redis.
        :param course_id: ID курса.
        :param user_id: tg_ID пользователя.
        """

        try:
            await self.redis_client.hset(f'{user_id}', course_id)
            logger_utils.info(f'Данные сохранены: {user_id}')
        except Exception as err:
            logger_utils.error(f'Ошибка при сохранении данных в Redis: {err}',
                               exc_info=True)

    @staticmethod
    async def check_cert_in_stepik(stepik_user_id: str, course_id: str,
                                   access_token: str) -> bool:
        """
        Проверяет наличие сертификата у пользователя на Stepik.
        :param stepik_user_id: ID пользователя на Stepik.
        :param course_id: ID курса.
        :param access_token: Токен доступа Stepik API.
        :return: True, если сертификат найден, иначе False.
        """
        page_number = 1
        while True:
            try:
                api_url = f'https://stepik.org/api/certificates?user={stepik_user_id}&page={page_number}'
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

    @staticmethod
    def sync_generate_certificate(data: dict[str, str],
                                  w_text: bool = False) -> tuple[str, str] | None:
        """
        Синхронная функция для генерации сертификата.
        :param data: Данные для генерации сертификата.
        :param w_text: Флаг для добавления водяного знака.
        :return: Путь к сгенерированному файлу сертификата.
        """
        logger_utils.debug('Entry')

        try:
            # 1. Извлечение данных из state_data
            user_name = data.get('full_name')
            number = data.get('end_number')
            course = BUTT_COURSES[data.get('course')]
            logger_utils.debug(f'{course=}')
            gender = data.get('gender')

            # Проверка значений gender и course
            if gender not in ('female', 'male'):
                logger_utils.error(f"Неизвестное значение gender: {gender}")
                raise ValueError(f"Неизвестное значение gender: {gender}")

            if course not in ('Лучший по Python.Часть 1', 'Лучший по Python.Часть 2'):
                logger_utils.error(f"Неизвестное значение course: {course}")
                raise ValueError(f"Неизвестное значение course: {course}")

        except KeyError as err:
            logger_utils.error(
                f"Ошибка при извлечении данных из state_data: {err}",
                exc_info=True)
            return None
        except Exception as err:
            logger_utils.error(
                f"Неизвестная ошибка при извлечении данных из state_data: {err}",
                exc_info=True)
            return None

        # 2. Определение путей к файлам
        try:
            local_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..', 'static'))
            base_dir = os.getenv('CERTIFICATE_DATA_DIR', local_path)

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

            # Проверка, что template_name не равен None
            if template_name is None:
                logger_utils.error(
                    f"Не удалось определить шаблон для gender={gender}, course={course}")
                raise ValueError("Имя шаблона не может быть None")

            logger_utils.debug(f"Выбран шаблон: {template_name}")

            font_path = os.path.join(base_dir, 'Bitter-Regular.ttf')
            template_file = os.path.join(base_dir, template_name)
            output_file = os.path.join(base_dir, f'BestInPython_{number}.pdf')

            if not os.path.exists(font_path):
                raise FileNotFoundError(f"Файл шрифта не найден: {font_path}")

        except FileNotFoundError as err:
            logger_utils.error(f"Ошибка при определении путей: {err}",
                               exc_info=True)
            return None
        except Exception as err:
            logger_utils.error(
                f"Неизвестная ошибка при определении путей: {err}",
                exc_info=True)
            return None

        # 3. Регистрация шрифта
        try:
            pdfmetrics.registerFont(TTFont('BitterReg', font_path))
        except Exception as err:
            logger_utils.error(f"Ошибка при регистрации шрифта: {err}",
                               exc_info=True)
            return None

        # 4. Работа с PDF
        try:
            light_gray = Color(230 / 255, 230 / 255, 230 / 255)
            watermark_text = 'TEST VERSION'
            reader = PdfReader(template_file)
            writer = PdfWriter()

            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=letter)
                font_size = 16

                if len(user_name) in (24, 25):
                    font_size = 15
                elif len(user_name) in (26, 27):
                    font_size = 14
                elif len(user_name) in (28, 29, 30):
                    font_size = 13

                text_width = can.stringWidth(user_name, 'BitterReg', font_size)
                can.setFont('BitterReg', font_size)
                page_width = letter[0]
                x_position = (page_width - text_width) / 2 + 155
                can.drawString(x_position, 306, user_name)
                can.setFont('BitterReg', 21)
                can.setFillColor(light_gray)
                can.drawString(440, 373, number)

                if w_text:
                    can.setFillColor(Color(0.3, 0, 0, alpha=0.7))
                    can.setFont('Helvetica', 50)
                    can.rotate(45)
                    can.drawString(110, 60, watermark_text)

                can.showPage()
                can.save()
                packet.seek(0)
                new_pdf = PdfReader(packet)
                page.merge_page(new_pdf.pages[0])
                writer.add_page(page)

            with open(output_file, 'wb') as fh:
                writer.write(fh)

        except Exception as err:
            logger_utils.error(f"Ошибка при работе с PDF: {err}", exc_info=True)
            return None

        # 5. Возврат результата
        return output_file, template_name

    @staticmethod
    def sync_exists_certificate(data: dict[str, str], w_text: bool = False):
        logger_utils.debug(f'Entry')
        logger_utils.debug(f'{data=}')

        try:
            local_path = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), '..', 'static'))
            base_dir = os.getenv('CERTIFICATE_DATA_DIR', local_path)

            template_name = data.get('template_name')
            user_name = data.get('full_name')
            cert_number = data.get('cert_number')

            font_path = os.path.join(base_dir, 'Bitter-Regular.ttf')
            template_file = os.path.join(base_dir, template_name)
            output_file = os.path.join(base_dir, f'BestInPython_{cert_number}.pdf')

            if not os.path.exists(font_path):
                raise FileNotFoundError(f"Файл шрифта не найден: {font_path}")
        except FileNotFoundError as err:
            logger_utils.error(f"Ошибка при определении путей: {err}",
                               exc_info=True)
            return None
        except Exception as err:
            logger_utils.error(
                    f"Неизвестная ошибка при определении путей: {err}",
                    exc_info=True)
            return None

        # 3. Регистрация шрифта
        try:
            pdfmetrics.registerFont(TTFont('BitterReg', font_path))
        except Exception as err:
            logger_utils.error(f"Ошибка при регистрации шрифта: {err}",
                               exc_info=True)
            return None

        # 4. Работа с PDF
        try:
            light_gray = Color(230 / 255, 230 / 255, 230 / 255)
            watermark_text = 'TEST VERSION'
            reader = PdfReader(template_file)
            writer = PdfWriter()

            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=letter)
                font_size = 16

                if len(user_name) in (24, 25):
                    font_size = 15
                elif len(user_name) in (26, 27):
                    font_size = 14
                elif len(user_name) in (28, 29, 30):
                    font_size = 13

                text_width = can.stringWidth(user_name, 'BitterReg', font_size)
                can.setFont('BitterReg', font_size)
                page_width = letter[0]
                x_position = (page_width - text_width) / 2 + 155
                can.drawString(x_position, 306, user_name)
                can.setFont('BitterReg', 21)
                can.setFillColor(light_gray)
                can.drawString(440, 373, cert_number)

                if w_text:
                    can.setFillColor(Color(0.3, 0, 0, alpha=0.7))
                    can.setFont('Helvetica', 50)
                    can.rotate(45)
                    can.drawString(110, 60, watermark_text)

                can.showPage()
                can.save()
                packet.seek(0)
                new_pdf = PdfReader(packet)
                page.merge_page(new_pdf.pages[0])
                writer.add_page(page)

            with open(output_file, 'wb') as fh:
                writer.write(fh)
        except Exception as err:
            logger_utils.error(f"Ошибка при работе с PDF: {err}", exc_info=True)
            return None
        # 5. Возврат результата
        return output_file

    async def generate_certificate(
            self, state_data: FSMContext, type_update, w_text: bool = False,
            exist_cert=False):
        """
        Асинхронная обёртка для генерации сертификата.
        :param type_update: Тип апдэйта.
        :param exist_cert: Флаг существования сертификата.
        :param state_data: Данные для генерации сертификата.
        :param w_text: Флаг для добавления водяного знака.
        :return: Путь к сгенерированному файлу сертификата.
        """
        logger_utils.debug(f'Entry')

        data = await state_data.get_data()
        user_tg_id = str(type_update.from_user.id)
        course_id = data.get('course').split('_')[-1]

        if exist_cert:
            try:
                user_data = await self.redis_client.hget(user_tg_id, course_id)
                logger_utils.debug(f'{user_data=}')

                cert_number, full_name, template = user_data.split(':')
                logger_utils.debug(f'{cert_number}-{full_name}-{template}')
                data.update({'template_name': template,
                             'cert_number': cert_number, 'full_name': full_name})

            except Exception:
                logger_utils.error(f'Не удалось получить данные пользователя '
                                   f'из Redis хранилища', exc_info=True)
                raise
            output_file = await asyncio.to_thread(
                self.sync_exists_certificate, data, w_text)
            logger_utils.debug(f'Exit')
            return output_file

        try:
            # Выполняем синхронную операцию в отдельном потоке
            output_file, template_name = await asyncio.to_thread(self.sync_generate_certificate,
                                                                 data, w_text)
            # Сохраняем данные в Redis
            cert_number = await state_data.get_value('end_number')
            full_name = await state_data.get_value('full_name')
            logger_utils.debug(f'{user_tg_id=}\n'
                               f'{course_id=}\n'
                               f'{cert_number=}\n'
                               f'{full_name=}\n'
                               f'{user_tg_id}={cert_number}:{full_name}:{template_name}')

            await self.redis_client.hset(name=user_tg_id,
                                         key=course_id,
                                         value=f'{cert_number}:'
                                               f'{full_name}:'
                                               f'{template_name}')
            await self.redis_client.set('info_data_user', f'TG_ID-{user_tg_id}:'
                                    f'{await get_username(type_update)}:'
                                    f'{cert_number}:{full_name}:{template_name}')

            logger_utils.debug(f'Exit')
            return output_file

        except Exception as err:
            logger_utils.error(f'{err=}', exc_info=True)
            logger_utils.debug(f'Exit')
            raise

    async def send_certificate(self, clbk: CallbackQuery, output_file: str,
                               state: FSMContext) -> None:
        """
        Отправляет сертификат пользователю, и удаляет файл после отправки.
        :param state:
        :param clbk: CallbackQuery от пользователя.
        :param output_file: Путь к файлу сертификата.
        """
        msg_processor = MessageProcessor(clbk, state)
        try:
            # Проверяем, существует ли файл
            if not os.path.exists(output_file):
                logger_utils.error(f"Файл {output_file} не найден.")
                return

            # Отправка файла пользователю
            pdf_file = FSInputFile(output_file)
            data = await self.redis_client.hget(name=str(clbk.from_user.id),
                                               key=str(await state.get_value(
                                                       'course_id')))
            await clbk.message.answer_document(pdf_file,
                                               caption='Ваш сертификат готов! 🎉\n'
                                               'Желаем удачи в дальнейшем'
                                                       ' обучении!🤓')

            # Логируем успешную отправку
            logger_utils.info(f'Выдан сертификат '
                              f'{await self.redis_client.get('info_data_user')}')

        except Exception as err:
            logger_utils.error(f"Ошибка при отправке файла: {err}",
                               exc_info=True)
            value = await clbk.message.answer('Что-то пошло не так, сообщите'
                                      ' администратору.')
            await msg_processor.save_msg_id(value, msgs_for_del=True)
        finally:
            # Удаляем файл после отправки
            try:
                os.remove(output_file)
                logger_utils.debug(f"Файл {output_file} удалён.")
            except Exception as err:
                logger_utils.error(
                    f"Ошибка при удалении файла {output_file}: {err}")


@dataclass
class MessageProcessor:
    """
    Class for managing and processing chat messages.
    _message (Message | CallbackQuery): The message or callback query object.
    _state (FSMContext): The finite state machine context.
    """
    _type_update: Message | CallbackQuery
    _state: FSMContext

    async def deletes_messages(self,
                               msg_remove: str = str | None,
                               msgs_for_del=False,
                               msgs_remove_kb=False) -> None:
        """
        Deleting messages from a chat based on passed parameters.
        This method removes various types of messages from a chat.
        Messages are deleted only if the corresponding parameters
        are set to True.
        If no parameters are specified, the method does not perform any actions.
        :param msg_remove: Key for remove msg.
        :param msgs_for_del:
        :param msgs_remove_kb:
        :return: None
        """
        logger_utils.debug(f'Entry')

        if isinstance(self._type_update, Message):
            chat_id = self._type_update.chat.id
        else:
            chat_id = self._type_update.message.chat.id

        kwargs: dict = {
                'msgs_for_del': msgs_for_del,
                'msgs_remove_kb': msgs_remove_kb}

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
            self, value: Message | CallbackQuery,
            msg_remove: str | None = None,
            msgs_for_del=False,
            msgs_remove_kb=False) -> None:
        """
        :param msg_remove: key for remove message on ID.
        :param value: Message | CallbackQuery.
        :param msgs_for_del:
        :param msgs_remove_kb:
        :return: None
        """
        logger_utils.debug('Entry')
        if key := msg_remove:
            await self._state.update_data(
                    {key: str(self._type_update.message_id)})

        flags: dict = {
                'msgs_for_del': msgs_for_del,
                'msgs_remove_kb': msgs_remove_kb}

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

    async def delete_message(self, key='msg_del_on_key') -> None:
        """
        Удаляет сообщение, используя указанный ключ. Метод извлекает данные из
        состояния и использует их для удаления сообщения с указанным ключом.
        Args: key (str): Ключ, по которому будет найдено сообщение
        удаление. По умолчанию «msg_id_for_del». Возвращает: None.
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
    async def deletes_msg_a_delay(value: Message,
                                  delay: int, indication=False) -> None:
        """
         Deletes a message after a specified time interval.
         Arguments: value (types.Message): The message to delete.
                    delay (int): Time in seconds before the message is deleted.
                    returns: None
        :param indication: Bool
        :param value: Message
        :param delay: int
        :return: None
        """
        if not indication:
            await asyncio.sleep(delay)
            await value.delete()
            return

        # Сохраняем оригинальный текст сообщения
        original_text = value.text
        try:
            # Обратный отсчет от delay до 1
            for remaining in range(delay, 0, -1):
                # Обновляем текст сообщения с оставшимся временем
                await value.edit_text(
                    f"{original_text}\n\nУдалится через: {remaining} сек...")
                await asyncio.sleep(1)
        except Exception as e:
            logger_utils.error(f"Ошибка при обновлении сообщения: {e}",
                               exc_info=True)
        finally:
            await value.delete()

    async def send_message_with_delay(
            self, chat_id: int, text: str, delay: int, preview_link: str) -> Message:
        """
        Sends a message with a specified delay.
        :param chat_id: The ID of the chat where the message will be sent.
        :param text:
        :param delay: The delay in seconds before sending the message.
        :param preview_link: Link for a preview.
        :return Message: Message: The sent message object.
        """
        logger_utils.debug(f'Entry')
        await asyncio.sleep(delay)

        # Send the message
        message = await self._type_update.bot.send_message(
                chat_id=chat_id, text=text,
                link_preview_options=LinkPreviewOptions(url=preview_link))

        logger_utils.debug(f'Exit')
        return message


async def shifts_the_date_forward(days: int = 10):
    expire_date = datetime.now() + timedelta(days=days)
    months: dict[int, str] = {1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
            5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа', 9: 'сентября',
            10: 'октября', 11: 'ноября', 12: 'декабря'}
    return f'{expire_date.day} {months[expire_date.month]}'
