import logging

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.buttons import BUTT_BACK, BUTT_CANCEL

logger_kb_utils = logging.getLogger(__name__)


def create_inline_kb(
        width: int = 1, *args, cancel_butt=True, back=False,
        reverse_size_text=False, url_buttons: dict = None, **kwargs) -> (
        InlineKeyboardMarkup):
    """
    Генерация инлайн-клавиатур на лету.
    Параметры:
        width (int): Количество кнопок в строке для маленьких кнопок.
        *args: Аргументы для кнопок с callback_data.
        cancel_butt (bool): Добавлять ли кнопку "Отмена".
        back (bool): Добавлять ли кнопку "Назад".
        webapp (bool): Добавлять ли кнопку с WebApp (не реализовано в этом
        примере).
        reverse_size_text (bool): Обратный порядок добавления больших и
        маленьких кнопок.
        url_buttons (dict): Словарь с текстом кнопок и ссылками (например,
        {"Текст": "URL"}).
        **kwargs: Именованные аргументы для кнопок с callback_data.
    Возвращает:
        InlineKeyboardMarkup: Объект клавиатуры.
    """
    kb_builder = InlineKeyboardBuilder()
    big_text: list[InlineKeyboardButton] = []
    small_text: list[InlineKeyboardButton] = []

    if args:
        for button in args:
            if len(button) > 16:
                big_text.append(InlineKeyboardButton(
                        text=BUTT_CANCEL[button] if BUTT_CANCEL.get(
                                button) else button, callback_data=button))
            else:
                small_text.append(InlineKeyboardButton(
                        text=BUTT_CANCEL[button] if BUTT_CANCEL.get(
                                button) else button, callback_data=button))

    if kwargs:
        for button, text in kwargs.items():
            if len(text) > 16:
                big_text.append(
                        InlineKeyboardButton(text=text, callback_data=button))
            else:
                small_text.append(
                        InlineKeyboardButton(text=text, callback_data=button))
    if not reverse_size_text:
        kb_builder.row(*big_text, width=1)
        kb_builder.row(*small_text, width=width)
    else:
        kb_builder.row(*small_text, width=width)
        kb_builder.row(*big_text, width=1)

    # Добавляет ссылки в кнопки(если они есть)
    if url_buttons:
        url_buttons_list = [InlineKeyboardButton(text=text, url=url) for
                text, url in url_buttons.items()]
        kb_builder.row(*url_buttons_list, width=1)

    if cancel_butt:
        kb_builder.row(InlineKeyboardButton(text=BUTT_CANCEL['cancel'],
                                            callback_data='/cancel'))
    if back:
        kb_builder.row(
            InlineKeyboardButton(text=BUTT_BACK['back'], callback_data='back'))

    return kb_builder.as_markup()
