import logging

from aiogram import Router
from aiogram.filters import StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from filters.filters import (
    CallBackFilter,
    IsAdmins,
    IsPrivateChat,
)
from states.states import MakeCert

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


@router.message(StateFilter(MakeCert.fill_link_to_stepik_profile))
async def msg_fill_link_to_stepik_profile(
    msg: Message, state: FSMContext
) -> None:
    logger.debug('Entry')

    logger.debug('Exit')
