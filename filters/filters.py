import logging
import re

from aiogram.filters import BaseFilter
from aiogram.types import Message

logger_filters = logging.getLogger(__name__)


class IsAdmin(BaseFilter):
    async def __call__(self, msg: Message, superadmin) -> bool:
        logger_filters.debug('Entry')
        user_id = str(msg.from_user.id)
        logger_filters.debug(f'In {__class__.__name__}:{user_id=}'
                             f':{superadmin=}\n{user_id == superadmin=}')
        logger_filters.debug('Exit')
        return user_id == superadmin

class IsFullName(BaseFilter):
    async def __call__(self, msg: Message) -> bool:
        pattern = r'^[А-ЯA-Z][а-яa-z]+ [А-ЯA-Z][а-яa-z]+$'
        if re.match(pattern, msg.text):
            return True
        else:
            return False
