import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message
from redis import Redis

from config_data.config import Stepik
from filters.filters import (IsCorrectData, IsFullName, IsValidProfileLink)
from keyboards import (BUTT_COURSES,
                       BUTT_GENDER,
                       kb_back_cancel,
                       kb_butt_cancel,
                       kb_courses,
                       kb_end_quiz,
                       kb_select_gender)
from lexicon.lexicon_ru import LexiconRu
from keyboards.keyboards import kb_butt_quiz
from states.states import FSMQuiz
from utils import StepikService
from utils.utils import MessageProcessor

user_router = Router()
logger_user_hand = logging.getLogger(__name__)


@user_router.message(F.text == '/start')
async def cmd_start(msg: Message, state: FSMContext):
    msg_processor = MessageProcessor(msg, state)
    await msg_processor.deletes_messages(msgs_for_del=True, msgs_for_reset=True)
    await state.clear()
    value = await msg.answer(LexiconRu.text_survey, reply_markup=kb_butt_quiz)
    await msg_processor.save_msg_id(value, msgs_for_del=True,
                                    msgs_for_reset=True)


@user_router.callback_query(F.data == 'back',
                            StateFilter(FSMQuiz.fill_date_of_revocation))
async def clbk_back_fill_date(clbk: CallbackQuery, state: FSMContext):
    logger_user_hand.debug('Entry')
    try:
        await clbk.message.edit_text(LexiconRu.text_select_course,
                                     reply_markup=kb_courses)
        await state.set_state(FSMQuiz.fill_course)
        await clbk.answer()
    except Exception as err:
        logger_user_hand.error(f'{err=}')
    logger_user_hand.debug('Exit')


@user_router.callback_query(F.data == 'back', StateFilter(FSMQuiz.fill_course))
async def clbk_back_fill_course(clbk: CallbackQuery, state: FSMContext):
    await clbk.message.edit_text(LexiconRu.text_gender,
                                 reply_markup=kb_select_gender)
    await state.set_state(FSMQuiz.fill_gender)
    await clbk.answer()


@user_router.callback_query(F.data == 'back', StateFilter(FSMQuiz.fill_gender))
async def clbk_back_fill_(clbk: CallbackQuery, state: FSMContext):
    msg_processor = MessageProcessor(clbk, state)
    await msg_processor.deletes_messages(msgs_for_del=True)
    value = await clbk.message.edit_text(LexiconRu.text_sent_fullname,
                                         reply_markup=kb_butt_cancel)
    await msg_processor.save_msg_id(value, msgs_for_reset=True,
                                    msgs_for_del=True)
    await state.set_state(FSMQuiz.fill_full_name)
    await clbk.answer()


@user_router.callback_query(F.data == 'back',
                            StateFilter(FSMQuiz.fill_link_cert))
async def clbk_back_fill_link_cert(clbk: CallbackQuery, state: FSMContext):
    logger_user_hand.debug('Entry')
    msg_processor = MessageProcessor(clbk, state)
    # await msg_processor.deletes_messages(msgs_for_del=True)
    value = await clbk.message.edit_text(LexiconRu.text_course_number_done,
                                         reply_markup=kb_back_cancel)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMQuiz.fill_date_of_revocation)
    await clbk.answer()
    logger_user_hand.debug('Exit')


@user_router.callback_query(F.data == 'back', StateFilter(FSMQuiz.end))
async def clbk_back_end(clbk: CallbackQuery, state: FSMContext):
    logger_user_hand.debug('Entry')
    msg_processor = MessageProcessor(clbk, state)
    await msg_processor.deletes_messages(msgs_for_del=True)
    value = await clbk.message.edit_text(LexiconRu.text_data_done,
                                         reply_markup=kb_back_cancel)
    await msg_processor.save_msg_id(value, msgs_for_del=True,
                                    msgs_for_reset=True)
    await state.set_state(FSMQuiz.fill_link_cert)
    await clbk.answer()
    logger_user_hand.debug('Exit')


@user_router.message(StateFilter(default_state), F.content_type.in_(
        {"text", "sticker", "photo", "video", "document"}))
async def msg_other(msg: Message):
    await msg.delete()


@user_router.callback_query(F.data == '/cancel', ~StateFilter(default_state))
async def clbk_back(clbk: CallbackQuery, state: FSMContext):
    logger_user_hand.debug(f'Entry {clbk_back.__name__=}')
    msg_processor = MessageProcessor(clbk, state)

    try:
        await state.clear()
    except Exception as err:
        logger_user_hand.error(f'{err=}')

    value = await clbk.message.edit_text(LexiconRu.text_survey,
                                         reply_markup=kb_butt_quiz)
    await msg_processor.save_msg_id(value, msgs_for_reset=True,
                                    msgs_for_del=True)
    await clbk.answer()
    logger_user_hand.debug(f'Exit {clbk_back.__name__=}')


@user_router.callback_query(F.data == 'get_cert', StateFilter(default_state))
async def clbk_get_cert(clbk: CallbackQuery, state: FSMContext):
    msg_processor = MessageProcessor(clbk, state)
    logger_user_hand.debug(f'{await state.get_state()=}')
    value = await clbk.message.edit_text(LexiconRu.text_sent_fullname,
                                         reply_markup=kb_butt_cancel)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMQuiz.fill_full_name)
    await clbk.answer()


@user_router.callback_query(F.data.in_(BUTT_GENDER),
                            StateFilter(FSMQuiz.fill_gender))
async def clbk_sex(clbk: CallbackQuery, state: FSMContext):
    msg_processor = MessageProcessor(clbk, state)
    await msg_processor.deletes_messages(msgs_for_del=True)
    await state.update_data(gender=clbk.data)
    value = await clbk.message.edit_text(LexiconRu.text_select_course,
                                         reply_markup=kb_courses)
    await msg_processor.save_msg_id(value, msgs_for_reset=True)
    await state.set_state(FSMQuiz.fill_course)
    await clbk.answer()


@user_router.callback_query(F.data.in_(
        [name for name in BUTT_COURSES if name.startswith(('id_1', 'id_2'))]),
        StateFilter(FSMQuiz.fill_course))
async def clbk_select_course(clbk: CallbackQuery, state: FSMContext):
    await state.update_data(course=clbk.data)
    value = await clbk.message.edit_text(LexiconRu.text_course_number_done,
                                         reply_markup=kb_back_cancel)
    await MessageProcessor(clbk, state).save_msg_id(value, msgs_for_del=True,
                                                    msgs_for_reset=True)
    await state.set_state(FSMQuiz.fill_date_of_revocation)
    await clbk.answer()


@user_router.callback_query(F.data.in_([name for name in BUTT_COURSES if
        name.startswith(('id_3', 'id_4', 'id_5', 'id_6'))]),
        StateFilter(FSMQuiz.fill_course))
async def clbk_select_empty_course(clbk: CallbackQuery):
    await clbk.answer('Курс находиться в разработке', show_alert=True)


@user_router.message(
        StateFilter(FSMQuiz.fill_gender, FSMQuiz.fill_course, FSMQuiz.end),
        F.content_type.in_({"text", "sticker", "photo", "video", "document"}))
async def delete_unexpected_messages(msg: Message, state: FSMContext):
    """
    Удаляет сообщения пользователя, если он отправляет текст/медиа, вместо
    нажатия на кнопку.
    """
    logger_user_hand.debug(f"Перехвачено сообщение типа: {msg.content_type}")
    await msg.delete()
    msg_processor = MessageProcessor(msg, state)
    reminder = await msg.answer(
            "Пожалуйста, используйте кнопки для взаимодействия с ботом.")
    await msg_processor.deletes_msg_a_delay(reminder, delay=3)


@user_router.message(StateFilter(FSMQuiz.fill_full_name), IsFullName())
async def msg_full_name(msg: Message, state: FSMContext):
    await msg.delete()
    msg_processor = MessageProcessor(msg, state)
    logger_user_hand.debug(f'{await state.get_state()=}')
    await state.update_data(full_name=msg.text)
    logger_user_hand.debug(f'{await state.get_data()=}')
    await msg_processor.deletes_messages(msgs_for_del=True)
    value = await msg.answer(LexiconRu.text_gender,
                             reply_markup=kb_select_gender)
    await msg_processor.save_msg_id(value, msgs_for_reset=True)

    await state.set_state(FSMQuiz.fill_gender)


@user_router.message(StateFilter(FSMQuiz.fill_date_of_revocation),
                     IsCorrectData())
async def msg_sent_date(msg: Message, state: FSMContext, date: str):
    await msg.delete()
    logger_user_hand.debug('Entry')
    msg_processor = MessageProcessor(msg, state)
    await msg_processor.deletes_messages(msgs_for_del=True)
    await state.update_data(date=date)
    value = await msg.answer(LexiconRu.text_data_done,
                             reply_markup=kb_back_cancel)
    await msg_processor.save_msg_id(value, msgs_for_del=True,
                                    msgs_for_reset=True)
    await state.set_state(FSMQuiz.fill_link_cert)
    logger_user_hand.debug('Exit')


@user_router.callback_query(F.data == 'done', StateFilter(FSMQuiz.end))
async def clbk_done(
        clbk: CallbackQuery, state: FSMContext, redis_client: Redis,
        stepik: Stepik):
    logger_user_hand.debug(f'Entry')
    msg_processor = MessageProcessor(clbk, state)
    stepik_service = StepikService(stepik.client_id, stepik.client_cecret,
                                  redis_client)
    await clbk.answer("Данные проверяются…")
    value1 = await clbk.message.edit_text('Ваши данные проверяются✅\n'
                                          'Ожидайте выдачи сертификата🏆\n',
                                          reply_markup=kb_butt_quiz)

    stepik_user_id = await state.get_value('stepik_user_id')
    course_id = str(await state.get_value('course')).split('_')[-1]
    logger_user_hand.debug(f'{course_id=}')
    access_token = await stepik_service.get_stepik_access_token()
    certificates = await stepik_service.check_certificate(stepik_user_id,
                                                          course_id, access_token)
    if certificates:
        try:
            number = await redis_client.incr('cert_number')
            number_str = str(number).zfill(6)
            await state.update_data(number=number_str)
            logger_user_hand.debug(f'{number_str=}')
        except Exception as err:
            logger_user_hand.error(f'{err=}', exc_info=True)
            return

        try:
            # генерация сертификата
            path = await stepik_service.generate_certificate(state, w_text=True)
            logger_user_hand.debug(f'{path=}')
        except Exception as err:
            logger_user_hand.error(f'{err=}', exc_info=True)
            await clbk.message.answer('Произошла ошибка. Попробуйте позже.\n'
                                      'Или обратитесь к администратору.')
            return

        try:
            logger_user_hand.info(f'Выдан сертификат {number_str} '
                                  f'пользователю {clbk.from_user.first_name}'
                                  f':{clbk.from_user.id}')

            # отправка сертификата
            await stepik_service.send_certificate(clbk, path)
            value = await clbk.message.answer(LexiconRu.text_survey,
                                              reply_markup=kb_butt_quiz)
            await msg_processor.save_msg_id(value, msgs_for_reset=True,
                                            msgs_for_del=True)
            await msg_processor.deletes_msg_a_delay(value1, delay=5)
            logger_user_hand.debug(f'Exit {clbk_back.__name__=}')

        except Exception as err:
            logger_user_hand.error(f'{err=}', exc_info=True)
        finally:
            await state.clear()
            await clbk.answer()
    else:
        value = await clbk.message.answer('У вас пока нет сертификата этого'
                                          ' курса')
        await msg_processor.save_msg_id(value, msgs_for_del=True)
        value = await clbk.message.answer(LexiconRu.text_survey,
                                          reply_markup=kb_butt_quiz)
        await msg_processor.save_msg_id(value, msgs_for_reset=True,
                                        msgs_for_del=True)

        await state.clear()
        await clbk.answer()
    logger_user_hand.debug(f'Exit')


@user_router.message(StateFilter(FSMQuiz.fill_link_cert), IsValidProfileLink())
async def msg_sent_stepik_link(
        msg: Message, state: FSMContext, stepik_user_id: str):
    msg_processor = MessageProcessor(msg, state)
    # запись Stepik_user_id
    await state.update_data(stepik_user_id=stepik_user_id)
    await msg_processor.deletes_messages(msgs_for_del=True)

    text = (f'{'Имя:':<7}{await state.get_value('full_name')}\n'
            f'{'Пол:':<7}{BUTT_GENDER[await state.get_value('gender')]}\n'
            f'{'Курс:':<7}{BUTT_COURSES[await state.get_value('course')]}\n'
            f'Stepik_ID:   {await state.get_value('stepik_user_id')}\n'
            f'Дата отзыва: {await state.get_value('date')}')
    await state.set_state(FSMQuiz.end)
    await msg.delete()
    value = await msg.answer('Нажмите подтвердить, если все данные верны.\n\n'
                             f'<code>{text}</code>', reply_markup=kb_end_quiz)
    await msg_processor.save_msg_id(value, msgs_for_reset=True)
