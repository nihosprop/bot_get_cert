import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from filters.filters import IsPrivateChat
from keyboards.keyboards import kb_butt_quiz
from lexicon import LexiconRu
from utils import MessageProcessor

router = Router()
router.message.filter(IsPrivateChat())
logger = logging.getLogger(__name__)


@router.callback_query(F.data == 'exit')
async def clbk_exit(
        clbk: CallbackQuery,
        state: FSMContext,
        msg_processor: MessageProcessor):
    logger.debug('Entry')

    try:
        await msg_processor.deletes_messages(
            msgs_remove_kb=True,
            msgs_for_del=True)
    except Exception as err:
        logger.error(
            f'Ошибка при удалении kb {err.__class__.__name__}',
            exc_info=True)

    try:
        value = await clbk.message.answer(
            LexiconRu.text_survey,
            reply_markup=kb_butt_quiz,
            disable_web_page_preview=True)
    except Exception as err:
        logger.error(f'{err.__class__.__name__}', exc_info=True)
    else:
        await msg_processor.save_msg_id(value, msgs_for_del=True)
    await state.set_state(state=None)
    await clbk.answer()

    logger.debug('Exit')
