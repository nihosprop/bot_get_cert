import logging

from aiogram.fsm.state import StatesGroup, State

logger_states = logging.getLogger(__name__)

class FSMAdminPanel(StatesGroup):
    admin_menu = State()
    newsletter = State()

class FSMQuiz(StatesGroup):
    fill_full_name = State()
    fill_gender = State()
    fill_course = State()
    fill_date_of_revocation = State()
    fill_email = State()
    end = State()
    