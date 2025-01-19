import logging

from aiogram.fsm.state import StatesGroup, State

logger_states = logging.getLogger(__name__)

class FSMAdminPanel(StatesGroup):
    admin_menu = State()
    newsletter = State()
    