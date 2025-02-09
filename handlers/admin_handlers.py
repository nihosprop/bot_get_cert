import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from arq.connections import RedisSettings
from redis.asyncio import Redis

from filters.filters import IsAdmins
from keyboards import kb_butt_quiz
from keyboards.keyboards import kb_admin
from lexicon import LexiconRu
from queues.que_utils import mass_mailing
from states.states import FSMAdminPanel
from utils import MessageProcessor


admin_router = Router()
admin_router.message.filter(IsAdmins())

logger_admin = logging.getLogger(__name__)


@admin_router.message(F.text == '/admin')
async def cmd_admin(
        msg: Message, state: FSMContext, redis_data: Redis,
        msg_processor: MessageProcessor):
    keys = set(filter(lambda _id: _id.isdigit(), await redis_data.keys()))
    logger_admin.debug(f'{keys=}')

    await msg_processor.deletes_messages(msgs_for_del=True)
    await msg.delete()
    end_cert = str(await redis_data.get('end_number')).zfill(6)

    await msg.answer(LexiconRu.text_adm_panel.format(end_cert=end_cert),
                     reply_markup=kb_admin)
    await state.set_state(FSMAdminPanel.admin_menu)


@admin_router.callback_query(F.data == 'exit')
async def cmd_exit(
        clbk: CallbackQuery, state: FSMContext,
        msg_processor: MessageProcessor):
    await state.set_state(state=None)
    value = await clbk.message.edit_text(f'Вы вышли из админ-панели✅\n'
                                         f'{LexiconRu.text_survey}',
                                         reply_markup=kb_butt_quiz,
                                         disable_web_page_preview=True)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await clbk.answer()


@admin_router.callback_query(F.data == 'newsletter',
                            StateFilter(FSMAdminPanel.admin_menu))
async def cmd_exit(clbk: CallbackQuery, state: FSMContext):
    # await clbk.answer(f'Кнопка в разработке', show_alert=True)
    await clbk.message.edit_text(f'Введите сообщение для рассылки.\n'
                                 f'После отправки боту, начнется рассылка!')
    await state.set_state(FSMAdminPanel.newsletter)
    await clbk.answer()


@admin_router.message(StateFilter(FSMAdminPanel.newsletter))
async def other_msg(msg: Message, redis_data: Redis, redis_que: RedisSettings,
                    state: FSMContext):
    logger_admin.debug('Entry')

    msg_letter = msg.text
    user_ids = set(map(int, filter(lambda _id: _id.isdigit(),
    await redis_data.keys())))
    logger_admin.debug(f"IDs пользователей: {user_ids}")
    await msg.answer(f'Кол-во пользователей для рассылки: {len(user_ids)}')

    try:
        await mass_mailing(redis_que=redis_que, user_ids=user_ids,
                       message=msg_letter)
    except Exception as err:
        logger_admin.error(f'Ошибка: {err}', exc_info=True)

    end_cert = str(await redis_data.get('end_number')).zfill(6)

    await msg.answer(LexiconRu.text_adm_panel.format(end_cert=end_cert),
                     reply_markup=kb_admin)
    await state.set_state(FSMAdminPanel.admin_menu)

    logger_admin.debug('Exit')
