import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from lexicon.lexicon_ru import LexiconRu
from keyboards import kb_back

user_router = Router()
logger_user_hand = logging.getLogger(__name__)


@user_router.message(F.text == '/start')
async def cmd_start(msg: Message):
    await msg.answer('Меню', reply_markup=kb_menu)


@user_router.callback_query(F.data == 'back')
async def clbk_back(clbk: CallbackQuery):
    await clbk.message.edit_text(LexiconRu.text_word_guessed,
                                 reply_markup=kb_game)
    await clbk.answer()
