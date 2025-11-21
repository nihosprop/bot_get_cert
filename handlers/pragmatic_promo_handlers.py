import logging

from aiogram import F, Router
from aiogram.filters import StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from filters.filters import CallBackFilter
from keyboards import kb_create_promo, kb_pragmatic_proger_promocodes
from lexicon.lexicon_ru import LexiconRu
from states.states import FSMPragmaticPromoSG
from utils import get_username

router = Router()
router.callback_query.filter(
    or_f(
        StateFilter(FSMPragmaticPromoSG),
        CallBackFilter(
            clbk_data='courses_pragmatic_programmer')))
logger = logging.getLogger(__name__)


@router.callback_query(F.data == 'courses_pragmatic_programmer')
async def clbk_courses_pragmatic_programmer(
        clbk: CallbackQuery,
        state: FSMContext):
    logger.debug('Entry')
    logger.info(
        f'{await get_username(clbk)}:{clbk.from_user.id} entered'
        f'in Promo on Courses Pragmatic Proger')

    await clbk.message.edit_text(
        LexiconRu.text_promo_pragmatic_proger,
        reply_markup=kb_pragmatic_proger_promocodes,
        disable_web_page_preview=True)

    await state.set_state(FSMPragmaticPromoSG.choice_promocodes)
    await clbk.answer()
    logger.debug('Exit')

@router.callback_query(
    F.data == 'back',
    StateFilter(FSMPragmaticPromoSG.choice_promocodes))
async def clbk_back(
        clbk: CallbackQuery,
        state: FSMContext):
    logger.debug('Entry')

    await clbk.message.edit_text(
        LexiconRu.text_survey,
        reply_markup=kb_create_promo,
        disable_web_page_preview=True)
    await state.set_state(state=None)
    await clbk.answer()
    logger.info(
        f'{await get_username(clbk)}:{clbk.from_user.id} back to '
        f'start screen.')
    logger.debug('Exit')
