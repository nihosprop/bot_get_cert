import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message

from filters.filters import IsFullName
from keyboards import kb_select_sex, kb_butt_cancel
from lexicon.lexicon_ru import LexiconRu
from keyboards.keyboards import kb_quiz
from states.states import FSMQuiz
from utils.utils import MessageProcessor

user_router = Router()
logger_user_hand = logging.getLogger(__name__)


@user_router.message(F.text == '/start', StateFilter(default_state))
async def cmd_start(msg: Message):
    await msg.answer(LexiconRu.text_survey, reply_markup=kb_quiz)

@user_router.callback_query(F.data == '/cancel', ~StateFilter(default_state))
async def clbk_back(clbk: CallbackQuery, state: FSMContext):
    await clbk.message.edit_text(LexiconRu.text_survey, reply_markup=kb_quiz)
    await state.set_state(state=None)
    await clbk.answer()


@user_router.callback_query(F.data == 'start_quiz', StateFilter(default_state))
async def clbk_start_quiz(clbk: CallbackQuery, state: FSMContext):
    value = await clbk.message.edit_text(LexiconRu.text_sent_fullname,
                                         reply_markup=kb_butt_cancel)
    await MessageProcessor(clbk, state).save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMQuiz.fill_full_name)
    await clbk.answer()


@user_router.message(IsFullName(), StateFilter(FSMQuiz.fill_full_name))
async def msg_full_name(msg: Message, state: FSMContext):
    await MessageProcessor(msg, state).deletes_messages(msgs_for_del=True)
    await msg.delete()
    await msg.answer('Имя и Фамилия записаны✅\n'
                     'Выберите ваш пол', reply_markup=kb_select_sex)


@user_router.callback_query(F.data == 'back')
async def clbk_back(clbk: CallbackQuery):
    await clbk.message.edit_text('действие назад')
    await clbk.answer()

@user_router.message(F.text == '/reset')
async def cmd_reset(msg: Message, state: FSMContext):
    await state.set_state(state=None)
