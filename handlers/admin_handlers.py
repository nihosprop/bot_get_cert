import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from redis.asyncio import Redis

from filters.filters import IsAdmins
from keyboards import kb_butt_quiz
from keyboards.keyboards import kb_admin
from lexicon import LexiconRu
from states.states import FSMAdminPanel
from utils import MessageProcessor, get_username

admin_router = Router()
admin_router.message.filter(IsAdmins())

logger_admin = logging.getLogger(__name__)


@admin_router.message(F.text == '/admin')
async def cmd_admin(
        msg: Message, state: FSMContext, redis_data: Redis, admins,
        msg_processor: MessageProcessor):
    logger_admin.debug(f'Админы: {admins=}')
    await msg_processor.deletes_messages(msgs_for_del=True)
    await msg.delete()
    end_cert = str(await redis_data.get('end_number')).zfill(6)
    user_data = await redis_data.hgetall(str(msg.from_user.id))
    logger_admin.debug(f'Данные юзера: TD_ID-[{msg.from_user.id}:'
                       f'{await get_username(msg)}]:{user_data=}')

    await msg.answer(LexiconRu.text_adm_panel.format(end_cert=end_cert),
                     reply_markup=kb_admin)
    await state.set_state(FSMAdminPanel.admin_menu)


@admin_router.callback_query(F.data == 'exit')
async def cmd_exit(
        clbk: CallbackQuery, state: FSMContext, msg_processor: MessageProcessor):
    await state.set_state(state=None)
    value = await clbk.message.edit_text(f'Вы вышли из админ-панели✅\n'
                                         f'{LexiconRu.text_survey}',
                                         reply_markup=kb_butt_quiz,
                                         disable_web_page_preview=True)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await clbk.answer()


@admin_router.callback_query(F.data == 'newsletter',
                             StateFilter(FSMAdminPanel.admin_menu))
async def cmd_exit(clbk: CallbackQuery):
    await clbk.answer(f'Кнопка в разработке', show_alert=True)


@admin_router.message(
        StateFilter(FSMAdminPanel.admin_menu, FSMAdminPanel.newsletter))
async def other_msg(msg: Message):
    await msg.delete()
