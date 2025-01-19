import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from filters.filters import IsFullName
from lexicon.lexicon_ru import LexiconRu
from keyboards.keyboards import kb_quiz
from states.states import FSMQuiz


user_router = Router()
logger_user_hand = logging.getLogger(__name__)


@user_router.message(F.text == '/start')
async def cmd_start(msg: Message):
    await msg.answer(LexiconRu.text_survey, reply_markup=kb_quiz)

@user_router.callback_query(F.data == 'start_quiz')
async def clbk_start_quiz(clbk: CallbackQuery, state: FSMContext):
    await clbk.message.edit_text('Введите ваши Фамилию и Имя и отправьте боту.\n'
                                 'Пример:\n<code>Питон Джаваскриптович</code>')
    await state.set_state(FSMQuiz.fill_full_name)
    await clbk.answer()

@user_router.message(IsFullName(), StateFilter(FSMQuiz.fill_full_name))
async def msg_full_name(msg: Message):
    pass

@user_router.callback_query(F.data == 'back')
async def clbk_back(clbk: CallbackQuery):
    await clbk.message.edit_text('действие назад')
    await clbk.answer()
