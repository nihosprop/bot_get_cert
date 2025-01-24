import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, FSInputFile, Message
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
from utils.utils import MessageProcessor

promo_router = Router()
promo_router.callback_query.filter(F.data == 'get_promo')
logger_promo = logging.getLogger(__name__)


@promo_router.callback_query(F.data == 'get_promo')
async def temp(clbk: CallbackQuery):
    await clbk.answer('В разработке', show_alert=True)
