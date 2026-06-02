import logging

from aiogram import Router
from aiogram.filters import StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from filters.filters import (
    CallBackFilter,
    IsAdmins,
    IsFullName,
    IsPrivateChat,
    IsValidProfileLink,
)
from keyboards import kb_select_gender
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


@router.message(
    StateFilter(MakeCert.fill_link_to_stepik_profile), IsValidProfileLink()
)
async def msg_fill_link_to_stepik_profile(
    msg: Message,
    state: FSMContext,
    stepik_user_id: str,
) -> None:
    """
    Handles the stepik user link.

    Args:
        msg: The message containing the stepik user link.
        state: The current state of the FSM.
        stepik_user_id: The stepik user ID extracted from the link.

    Returns:
        None
    """
    logger.debug('Entry')

    if not msg.from_user:
        logger.warning('Message without user info received')
        return
    await state.update_data(stepik_user_id=stepik_user_id)
    logger.info(
        f'Ссылка записана:{msg.from_user.id}'
        f':{await get_username(msg)}:[{msg.text}]'
    )
    await state.set_state(state=MakeCert.fill_full_name)

    logger.debug('Exit')


@router.message(StateFilter(MakeCert.fill_full_name), IsFullName())
async def msg_fill_full_name(
    msg: Message,
    full_name: dict | bool,
    state: FSMContext,
    msg_processor: MessageProcessor,
) -> None:
    logger.debug('Entry')

    if not msg.from_user:
        logger.warning('Message without user info received')
        return

    logger.info(
        f'Корректное ФИО:{msg.from_user.id}'
        f':{await get_username(msg)}:{full_name}'
    )
    await msg.delete()
    await state.update_data(full_name=full_name)
    await msg_processor.deletes_messages(msgs_for_del=True)
    await msg.answer(LexiconRu.text_gender, reply_markup=kb_select_gender)
    await state.set_state(state=MakeCert.fill_gender)

    logger.debug('Exit')
