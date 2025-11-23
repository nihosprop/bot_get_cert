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
    fill_link_to_stepik_profile = State()
    data_confirm = State()

class FSMDzeranovPromo(StatesGroup):
    choice_promocodes = State()
    want_promocode_dzeranov = State()

class FSMPragmaticPromo(StatesGroup):
    choice_promocodes = State()

class FSMPragmaticGetCert(StatesGroup):
    fill_date_of_revocation = State()
    fill_link_to_stepik_profile = State()
