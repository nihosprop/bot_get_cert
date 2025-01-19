import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message


user_router = Router()
logger_user_hand = logging.getLogger(__name__)


@user_router.message(F.text == '/start')
async def cmd_start(msg: Message):
    await msg.answer('Анкета')


@user_router.callback_query(F.data == 'back')
async def clbk_back(clbk: CallbackQuery):
    await clbk.message.edit_text('действие назад')
    await clbk.answer()
