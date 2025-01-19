import logging

from aiogram import F, Router
from aiogram.types import Message

other_router = Router()
logger_user_hand = logging.getLogger(__name__)


@other_router.message()
async def msg_other(msg: Message):
    await msg.delete()
