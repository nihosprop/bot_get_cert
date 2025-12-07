import logging

from aiogram import F, Router
from aiogram.filters import or_f
from aiogram.types import Message

from utils import get_username

temp_router = Router()
temp_router.message.filter(or_f(F.new_chat_members, F.left_chat_member))

logger = logging.getLogger(__name__)


@temp_router.message(F.new_chat_members)
async def delete_join_message(msg: Message) -> None:
    logger.info(
        f'{await get_username(msg)}:{msg.from_user.id} joined the chat!'
    )
    try:
        await msg.delete()
    except Exception as e:
        logger.error(f'Не удалось удалить сообщение:ID[{msg.message_id}]:{e}')


@temp_router.message(F.left_chat_member)
async def delete_exit_message(msg: Message) -> None:
    logger.info(f'{await get_username(msg)}:{msg.from_user.id} exit the chat!')
    try:
        await msg.delete()
    except Exception as e:
        logger.error(f'Не удалось удалить сообщение: {e}')
