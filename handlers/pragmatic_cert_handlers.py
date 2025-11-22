import logging

from aiogram import Router, F
from aiogram.filters import StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from redis import Redis

from config_data.config import Stepik
from filters.filters import (IsPragmaticCoursesFilter,
    CallBackFilter,
    IsCorrectData)
from keyboards import kb_back_cancel, kb_courses
from lexicon import LexiconRu
from states.states import FSMPragmaticGetCert, FSMQuiz
from utils import get_username, StepikService, MessageProcessor

router = Router()
router.callback_query.filter(or_f(IsPragmaticCoursesFilter(),
                                  CallBackFilter('back')))
logger = logging.getLogger(__name__)


@router.callback_query(IsPragmaticCoursesFilter())
async def get_pragmatic_certificates(
        clbk: CallbackQuery,
        state: FSMContext,
        w_text: bool,
        stepik: Stepik,
        redis_data: Redis,
        msg_processor: MessageProcessor):
    logger.debug('Entry')

    tg_username = await get_username(clbk)
    stepik_service = StepikService(
        client_id=stepik.client_id,
        client_secret=stepik.client_secret,
        redis_client=redis_data)
    logger.warning(
        f'Нажатие на курс {clbk.data}:{clbk.from_user.id}:{tg_username}')

    tg_id = str(clbk.from_user.id)
    course_id = clbk.data
    logger.info(
        f'Проверка наличия серт:TG_ID[{tg_id}]'
        f':{tg_username}:CourseID[{clbk.data}]')

    cert: str | bool = await stepik_service.check_cert_in_user(tg_id, course_id)
    logger.debug(f'{cert=}')

    if cert:
        value = await clbk.message.edit_text(
            'У вас есть сертификат этого курса 🤓\nВысылаем...📜☺️\n')
        try:
            path = await stepik_service.generate_certificate(
                state_data=state,
                type_update=clbk,
                w_text=w_text,
                exist_cert=True)

            await stepik_service.send_certificate(
                clbk=clbk,
                output_file=path,
                state=state,
                is_copy=True,
                course_id=course_id)

        except Exception as err:
            logger.debug(f'{err.__class__.__name__}', exc_info=True)

        await msg_processor.deletes_msg_a_delay(value, delay=5)
        await state.clear()
        logger.debug('Exit')
        return

    logger.info(f'Сертификат ID:{clbk.data} у TG_ID:{tg_id}'
                f':{tg_username} на руках не обнаружен')

    await state.update_data(course=clbk.data)
    logger.debug(f'{await state.get_data()=}')

    value = await clbk.message.edit_text(
        LexiconRu.text_course_number_done,
        reply_markup=kb_back_cancel)

    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMPragmaticGetCert.fill_date_of_revocation)
    await clbk.answer()

    logger.info(f'State of {tg_username}:{await state.get_state()}')
    logger.debug('Exit')

@router.callback_query(F.data == 'back',
                       StateFilter(
                           FSMPragmaticGetCert.fill_date_of_revocation))
async def clbk_back_on_fill_course(clbk: CallbackQuery,
                                   state: FSMContext):
    logger.debug('Entry')

    await clbk.message.edit_text(LexiconRu.text_select_course,
                                     reply_markup=kb_courses)
    await state.set_state(FSMQuiz.fill_course)
    await clbk.answer()

    logger.debug('Exit')

@router.message(StateFilter(FSMPragmaticGetCert.fill_date_of_revocation),
                IsCorrectData())
async def msg_fill_date_revocation(msg: Message,
                                   state: FSMContext,
                                   date: str,
                                   msg_processor: MessageProcessor):
    logger.debug('Entry')

    await msg.delete()
    await msg_processor.deletes_messages(msgs_for_del=True)
    await state.update_data(date=date)

    logger.info(f'Дата {date} записана для TG_ID:{msg.from_user.id}'
                f':{await get_username(msg)}')

    value = await msg.answer(
        LexiconRu.text_data_done,
        reply_markup=kb_back_cancel,
        disable_web_page_preview=True)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMPragmaticGetCert.fill_link_to_stepik_profile)

    logger.debug('Exit')


@router.callback_query(F.data == 'back',
                       StateFilter(
                           FSMPragmaticGetCert.fill_link_to_stepik_profile))
async def clbk_back_to_fill_date_revocation(clbk: CallbackQuery,
                                            state: FSMContext):
    logger.debug('Entry')

    await clbk.message.edit_text(LexiconRu.text_course_number_done,
                                 reply_markup=kb_back_cancel)
    await state.set_state(FSMPragmaticGetCert.fill_date_of_revocation)
    await clbk.answer()

    logger.debug('Exit')







