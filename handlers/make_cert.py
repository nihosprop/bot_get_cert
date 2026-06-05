import logging

from aiogram import F, Router
from aiogram.filters import StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from filters.filters import (
    CallBackFilter,
    IsAdmins,
    IsBestPythonCoursesFilter,
    IsFullName,
    IsPrivateChat,
    IsValidProfileLink,
)
from keyboards import (
    BUTT_GENDER,
    kb_butt_cancel,
    kb_end_quiz,
    kb_select_gender,
)
from lexicon import LexiconRu
from states.states import MakeCert
from utils import MessageProcessor, get_username

router = Router()
router.callback_query.filter(
    or_f(
        IsAdmins(),
        CallBackFilter('back'),
        StateFilter(MakeCert()),
    )
)
router.message.filter(IsAdmins(), IsPrivateChat(), StateFilter(MakeCert()))
logger = logging.getLogger(__name__)


@router.callback_query(
    IsBestPythonCoursesFilter(), StateFilter(MakeCert.fill_course)
)
async def clbk_select_course(
    clbk: CallbackQuery,
    state: FSMContext,
    msg_processor: MessageProcessor,
) -> None:
    logger.debug('Entry')

    await state.update_data(course=clbk.data)
    if not clbk.message or not isinstance(clbk.message, Message):
        logger.warning('Callback message is None or inaccessible')
        return

    msg_obj = await clbk.message.edit_text(
        text='<b>Меню генерации сертификата.</b>\n'
        'ID курса записан.\n'
        'Отправьте ссылку Stepik на профиль ученика.',
        reply_markup=kb_butt_cancel,
    )

    await msg_processor.save_msg_id(value=msg_obj, msgs_for_del=True)
    await state.set_state(MakeCert.fill_link_to_stepik_profile)
    await clbk.answer()

    logger.debug('Exit')


@router.message(
    StateFilter(MakeCert.fill_link_to_stepik_profile), IsValidProfileLink()
)
async def msg_fill_link_to_stepik_profile(
    msg: Message,
    state: FSMContext,
    stepik_user_id: str,
    msg_processor: MessageProcessor,
) -> None:
    """
    Handles the stepik user link.

    Args:
        msg_processor: MessageProcessor instance.
        msg: The message containing the stepik user link.
        state: The current state of the FSM.
        stepik_user_id: The stepik user ID extracted from the link.

    Returns:
        None
    """
    logger.debug('Entry')

    await msg_processor.deletes_messages(msgs_for_del=True)
    if not msg.from_user:
        logger.warning('Message without user info received')
        return
    await state.update_data(stepik_user_id=stepik_user_id)
    logger.info(
        f'Ссылка записана:{msg.from_user.id}'
        f':{await get_username(msg)}:[{msg.text}]'
    )
    await msg.delete()
    await msg.answer(
        text='<b>Меню генерации сертификата.</b>\n' + LexiconRu.text_gender,
        reply_markup=kb_select_gender,
    )
    await state.set_state(state=MakeCert.fill_gender)

    logger.debug('Exit')


@router.callback_query(
    F.data.in_(BUTT_GENDER), StateFilter(MakeCert.fill_gender)
)
async def clbk_gender(
    clbk: CallbackQuery, state: FSMContext, msg_processor: MessageProcessor
) -> None:
    logger.debug('Entry')

    text_sent_fullname: str = (
        'Отправьте Имя и Фамилию ученика👇\n\n'
        'Допускаются двойные фамилии или имена, слитно'
        ' через дефис.\n'
        '<b>Количество символов ФИО не должно превышать '
        '30 вместе с пробелами</b>\n'
        'Примеры:\n'
        '1) Фамилия Имя\n'
        '2) Имя Фамилия\n'
        '3) Фамилия Имя Отчество\n'
        '4) Имя Фамилия Отчество\n'
        '5) Имя Фамилия1-Фамилия2\n'
        '6) Имя1-Имя2 Фамилия\n'
    )

    logger.info(
        f'Выбран пол:{clbk.from_user.id}'
        f':{await get_username(clbk)}:{clbk.data}'
    )
    logger.debug(f'{await state.get_state()=}')

    await state.update_data(gender=clbk.data)

    msg_jbj = await clbk.message.edit_text(
        text=text_sent_fullname, reply_markup=kb_butt_cancel
    )
    await msg_processor.save_msg_id(value=msg_jbj, msgs_for_del=True)
    await state.set_state(MakeCert.fill_full_name)
    await clbk.answer()

    logger.debug('Exit')


@router.message(StateFilter(MakeCert.fill_full_name), IsFullName())
async def msg_fill_full_name(
    msg: Message,
    full_name: dict | bool,
    state: FSMContext,
    msg_processor: MessageProcessor,
) -> None:
    logger.debug('Entry')

    await msg_processor.deletes_messages(msgs_for_del=True)

    if not msg.from_user:
        logger.warning('Message without user info received')
        return

    logger.info(
        f'Корректное ФИО:{msg.from_user.id}'
        f':{await get_username(msg)}:{full_name}'
    )
    await msg_processor.deletes_messages(msgs_for_del=True)
    # await msg.delete()
    await state.update_data(full_name=full_name)
    await msg.answer(
        'Проверьте данные и подтвердите.', reply_markup=kb_end_quiz
    )

    logger.debug('Exit')
