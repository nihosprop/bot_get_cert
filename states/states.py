import logging

from aiogram.fsm.state import StatesGroup, State

logger_states = logging.getLogger(__name__)

class FSMAdminPanel(StatesGroup):
    admin_menu = State()
    fill_newsletter = State()
    fill_confirm_newsletter = State()

class FSMQuiz(StatesGroup):
    fill_full_name = State()
    fill_gender = State()
    fill_course = State()
    fill_date_of_revocation = State()
    fill_link_cert = State()
    end = State()
