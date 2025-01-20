import logging

from keyboards.kb_utils import create_inline_kb
from keyboards.buttons import (ADMIN_PANEL_BUTT, BUTT_GENDER, BUTT_COURSES,
                               BUTT_DONE)

logger_keyboards = logging.getLogger(__name__)


class KeyBoards:

    @staticmethod
    def kb_game():
        pass


kb_butt_quiz = create_inline_kb(start_quiz='Начать', cancel_butt=False)
kb_butt_cancel = create_inline_kb(cancel_butt=True)

kb_admin = create_inline_kb(2, **ADMIN_PANEL_BUTT, cancel_butt=False)
kb_select_gender = create_inline_kb(2, **BUTT_GENDER, back=True)
kb_courses = create_inline_kb(**BUTT_COURSES, back=True)
kb_back_cancel = create_inline_kb(back=True, cancel_butt=True)
kb_end_quiz = create_inline_kb(**BUTT_DONE, cancel_butt=True, back=True)
