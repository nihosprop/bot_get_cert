import logging

from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import Message
other_router = Router()
logger_user_hand = logging.getLogger(__name__)


# @other_router.message(StateFilter(default_state))
# async def msg_other(msg: Message):
#     logger_user_hand.info('Entry other_hand')
#     await msg.delete()
#     logger_user_hand.info('Exit other_hand')
