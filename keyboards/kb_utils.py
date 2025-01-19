import logging

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.buttons import CANCEL_BUTT

logger_kb_utils = logging.getLogger(__name__)


def create_inline_kb(
        width: int = 1, *args, cancel_butt=True, back=False, webapp=False,
        reverse_size_text=False, **kwargs) -> InlineKeyboardMarkup:
    """Generates inline keyboards on the fly"""
    kb_builder = InlineKeyboardBuilder()
    big_text: list[InlineKeyboardButton] = []
    small_text: list[InlineKeyboardButton] = []

    # if immutable_buttons:
    #     buttons = [InlineKeyboardButton(text=text, callback_data=butt)
    #             for butt, text in kwargs.items()]
    #     kb_builder.row(*buttons, width=width)
    #     return kb_builder.as_markup()

    if args:
        for button in args:
            if len(button) > 16:
                big_text.append(InlineKeyboardButton(
                        text=CANCEL_BUTT[button] if CANCEL_BUTT.get(
                                button) else button, callback_data=button))
            else:
                small_text.append(InlineKeyboardButton(
                        text=CANCEL_BUTT[button] if CANCEL_BUTT.get(
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

    if cancel_butt:
        kb_builder.row(InlineKeyboardButton(text=CANCEL_BUTT['cancel'],
                                            callback_data='/cancel'))
    if webapp:
        kb_builder.row(
            InlineKeyboardButton(text="TestHTML", url='http://194.15.46.138/#'))

    return kb_builder.as_markup()
