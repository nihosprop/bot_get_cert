import logging

from aiogram import Router
from aiogram.filters import StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from filters.filters import IsPragmaticCoursesFilter
from utils import get_username

router = Router()
router.callback_query.filter(or_f(IsPragmaticCoursesFilter(), ))
logger = logging.getLogger(__name__)


@router.callback_query(IsPragmaticCoursesFilter())
async def clbk_pragmatic_courses(clbk: CallbackQuery):
    logger.debug('Entry')

    await clbk.answer('Сертификат в разработке 🛠️', show_alert=True)
    logger.warning(
        f'Нажатие на курс {clbk.data}:{clbk.from_user.id}:'
        f'{await get_username(clbk)}')

    logger.debug('Exit')
