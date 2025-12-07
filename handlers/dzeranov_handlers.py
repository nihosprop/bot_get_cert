import logging

from aiogram import F, Router
from aiogram.filters import StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from filters.filters import CallBackFilter
from keyboards import (
    kb_butt_quiz,
    kb_create_promo,
    kb_dzeranov_promocodes,
    kb_exit_back,
)
from lexicon.lexicon_ru import LexiconRu
from states.states import FSMDzeranovPromo
from utils import get_username

router = Router()
router.callback_query.filter(
    or_f(
        StateFilter(FSMDzeranovPromo),
        CallBackFilter(clbk_data='courses_joseph_dzeranov'),
    )
)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == 'courses_joseph_dzeranov')
async def clbk_courses_joseph_dzeranov(
    clbk: CallbackQuery, state: FSMContext
) -> None:
    logger.debug('Entry')
    logger.info(
        f'{await get_username(clbk)}:{clbk.from_user.id} entered'
        f'in Promo on Courses Joseph Dzeranov'
    )

    await clbk.message.edit_text(
        LexiconRu.text_promo_dzeranov,
        reply_markup=kb_dzeranov_promocodes,
        disable_web_page_preview=True,
    )
    await state.set_state(FSMDzeranovPromo.choice_promocodes)
    await clbk.answer()
    logger.debug('Exit')


@router.callback_query(
    F.data == 'back', StateFilter(FSMDzeranovPromo.choice_promocodes)
)
async def clbk_back(clbk: CallbackQuery, state: FSMContext) -> None:
    logger.debug('Entry')

    await clbk.message.edit_text(
        LexiconRu.text_survey,
        reply_markup=kb_create_promo,
        disable_web_page_preview=True,
    )
    await state.set_state(state=None)
    await clbk.answer()
    logger.info(
        f'{await get_username(clbk)}:{clbk.from_user.id} back to start screen.'
    )
    logger.debug('Exit')


@router.callback_query(
    StateFilter(FSMDzeranovPromo.choice_promocodes),
    F.data == 'want_promocode_dzeranov',
)
async def clbk_want_promocode_dzeranov(
    clbk: CallbackQuery, state: FSMContext
) -> None:
    logger.debug('Entry')

    text = (
        'Если хотите получить скидку на любой другой курс Иосифа, '
        'то напишите <a href="https://t.me/somevanya">Ване</a> в личку'
        ' Он всё организует 😊'
    )
    await state.set_state(FSMDzeranovPromo.want_promocode_dzeranov)
    await clbk.message.edit_text(text=text, reply_markup=kb_exit_back)
    await clbk.answer()

    logger.debug('Exit')


@router.callback_query(
    StateFilter(FSMDzeranovPromo.want_promocode_dzeranov), F.data == 'back'
)
async def clbk_back_want_promocode_dzeranov(
    clbk: CallbackQuery, state: FSMContext
) -> None:
    logger.debug('Entry')

    await clbk.message.edit_text(
        LexiconRu.text_promo_dzeranov,
        reply_markup=kb_dzeranov_promocodes,
        disable_web_page_preview=True,
    )
    await state.set_state(FSMDzeranovPromo.choice_promocodes)
    await clbk.answer()

    logger.debug('Exit')


@router.callback_query(F.data == 'exit')
async def clbk_exit(clbk: CallbackQuery, state: FSMContext) -> None:
    logger.debug('Entry')

    await clbk.message.edit_text(
        LexiconRu.text_survey,
        reply_markup=kb_butt_quiz,
        disable_web_page_preview=True,
    )
    await state.set_state(state=None)
    await clbk.answer()
    logger.info(
        f'{await get_username(clbk)}:{clbk.from_user.id} back to start screen.'
    )

    logger.debug('Exit')
