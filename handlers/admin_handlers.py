import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from filters.filters import IsAdmin
from keyboards.keyboards import kb_admin, kb_back
from lexicon import LexiconRu
from states.states import FSMAdminPanel

admin_router = Router()
admin_router.message.filter(IsAdmin())

logger_admin = logging.getLogger(__name__)


@admin_router.message(F.text == '/admin')
async def cmd_admin(msg: Message, state: FSMContext):
    await msg.delete()
    await msg.answer(LexiconRu.text_adm_panel, reply_markup=kb_admin)
    await state.set_state(FSMAdminPanel.admin_menu)


@admin_router.callback_query(F.data == 'exit')
async def cmd_exit(clbk: CallbackQuery, state: FSMContext):
    await state.set_state(state=None)
    await clbk.message.edit_text(f'Вы вышли из админ-панели✅')
    await clbk.answer()


@admin_router.message(FSMAdminPanel.newsletter)
async def msg_newsletter(msg: Message, state: FSMContext):
    # await MessageProcessor(msg, state).broadcast(text=msg.text)
    await msg.delete()
    await msg.answer('Рассылка произведена✅', reply_markup=kb_admin)
    await state.set_state(FSMAdminPanel.admin_menu)
