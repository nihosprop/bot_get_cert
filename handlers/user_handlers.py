import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message

from filters.filters import IsCorrectData, IsCorrectEmail, IsFullName
from keyboards import (BUTT_COURSES,
                       BUTT_GENDER,
                       kb_back_cancel,
                       kb_butt_cancel,
                       kb_courses,
                       kb_select_gender,
                       kb_end_quiz)
from lexicon.lexicon_ru import LexiconRu
from keyboards.keyboards import kb_butt_quiz
from states.states import FSMQuiz
from utils.utils import MessageProcessor

user_router = Router()
logger_user_hand = logging.getLogger(__name__)


@user_router.message(F.text == '/reset')
async def cmd_reset(msg: Message, state: FSMContext):
    await msg.delete()
    await state.set_state(state=None)
    await msg.answer(LexiconRu.text_survey, reply_markup=kb_butt_quiz)


@user_router.message(F.text == '/start', StateFilter(default_state))
async def cmd_start(msg: Message):
    await msg.answer(LexiconRu.text_survey, reply_markup=kb_butt_quiz)


@user_router.callback_query(F.data == '/cancel', ~StateFilter(default_state))
async def clbk_back(clbk: CallbackQuery, state: FSMContext):
    await clbk.message.edit_text(LexiconRu.text_survey,
                                 reply_markup=kb_butt_quiz)
    await state.clear()
    await clbk.answer()


@user_router.message(StateFilter(default_state))
async def msg_other(msg: Message):
    await msg.delete()


@user_router.callback_query(F.data == 'start_quiz', StateFilter(default_state))
async def clbk_start_quiz(clbk: CallbackQuery, state: FSMContext):
    value = await clbk.message.edit_text(LexiconRu.text_sent_fullname,
                                         reply_markup=kb_butt_cancel)
    await MessageProcessor(clbk, state).save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMQuiz.fill_full_name)
    await clbk.answer()


@user_router.callback_query(F.data == 'back', StateFilter(FSMQuiz.fill_gender))
async def clbk_back_fill_(clbk: CallbackQuery, state: FSMContext):
    await clbk.message.edit_text(LexiconRu.text_sent_fullname,
                                 reply_markup=kb_butt_cancel)
    await state.set_state(FSMQuiz.fill_full_name)
    await clbk.answer()


@user_router.message(IsFullName(), StateFilter(FSMQuiz.fill_full_name))
async def msg_full_name(msg: Message, state: FSMContext):
    await state.update_data(full_name=msg.text)
    text = f'{await state.get_value('full_name')}'
    logger_user_hand.debug(f'{text=}')
    logger_user_hand.debug(f'{await state.get_data()=}')
    await MessageProcessor(msg, state).deletes_messages(msgs_for_del=True)
    await msg.delete()
    await msg.answer(LexiconRu.text_gender, reply_markup=kb_select_gender)
    await state.set_state(FSMQuiz.fill_gender)


@user_router.message(StateFilter(FSMQuiz.fill_gender))
async def msg_other_fill_gender(msg: Message):
    await msg.delete()


@user_router.callback_query(F.data.in_(BUTT_GENDER),
                            StateFilter(FSMQuiz.fill_gender))
async def clbk_sex(clbk: CallbackQuery, state: FSMContext):
    value = clbk.data  # gender
    logger_user_hand.debug(f'{value}')
    await clbk.message.edit_text(LexiconRu.text_select_course,
                                 reply_markup=kb_courses)
    await state.set_state(FSMQuiz.fill_course)
    await clbk.answer()


@user_router.callback_query(F.data == 'back', StateFilter(FSMQuiz.fill_course))
async def clbk_back_fill_course(clbk: CallbackQuery, state: FSMContext):
    await clbk.message.edit_text(LexiconRu.text_gender,
                                 reply_markup=kb_select_gender)
    await state.set_state(FSMQuiz.fill_gender)
    await clbk.answer()


@user_router.callback_query(
        F.data.in_([name for name in BUTT_COURSES if name.endswith(('1', '2'))]),
        StateFilter(FSMQuiz.fill_course))
async def clbk_select_course(clbk: CallbackQuery, state: FSMContext):
    course_number = clbk.data
    # запись номера курса в контекст
    await state.update_data(course_number=course_number)
    await clbk.message.edit_text(LexiconRu.text_course_number_done,
                                 reply_markup=kb_back_cancel)
    await state.set_state(FSMQuiz.fill_date_of_revocation)
    await clbk.answer()


@user_router.callback_query(F.data.in_(
        [name for name in BUTT_COURSES if name.endswith(('3', '4', '5'))]),
        StateFilter(FSMQuiz.fill_course))
async def clbk_select_empty_course(clbk: CallbackQuery):
    await clbk.answer('Курс находиться в разработке', show_alert=True)


@user_router.callback_query(F.data == 'back',
                            StateFilter(FSMQuiz.fill_date_of_revocation))
async def clbk_back_fill_date(clbk: CallbackQuery, state: FSMContext):
    logger_user_hand.debug('Entry')
    await clbk.message.edit_text(LexiconRu.text_select_course,
                                 reply_markup=kb_courses)
    await state.set_state(FSMQuiz.fill_course)
    await clbk.answer()
    logger_user_hand.debug('Exit')


@user_router.message(IsCorrectData(),
                     StateFilter(FSMQuiz.fill_date_of_revocation))
async def msg_sent_date(msg: Message, state: FSMContext, date: str):
    logger_user_hand.debug('Entry')
    await state.update_data(date=date)
    await msg.delete()
    value = await msg.answer(LexiconRu.text_data_done,
                             reply_markup=kb_back_cancel)
    await MessageProcessor(msg, state).save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMQuiz.fill_email)
    logger_user_hand.debug('Exit')


@user_router.callback_query(F.data == 'back', StateFilter(FSMQuiz.fill_email))
async def clbk_back_fill_date(clbk: CallbackQuery, state: FSMContext):
    logger_user_hand.debug('Entry')
    value = await clbk.message.edit_text(LexiconRu.text_course_number_done,
                                         reply_markup=kb_back_cancel)
    await MessageProcessor(clbk, state).save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMQuiz.fill_date_of_revocation)
    await clbk.answer()
    logger_user_hand.debug('Exit')


@user_router.message(IsCorrectEmail(), StateFilter(FSMQuiz.fill_email))
async def msg_sent_email(msg: Message, state: FSMContext, email: str):
    await MessageProcessor(msg, state).deletes_messages(msgs_for_del=True)
    await state.update_data(email=email)
    await msg.delete()
    await msg.answer('Email записан✅\n'
                     'Нажмите подтвердить, если все данные верны.',
                     reply_markup=kb_end_quiz)




