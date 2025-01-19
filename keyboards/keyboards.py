import logging


from keyboards.kb_utils import create_inline_kb
from keyboards.buttons import ADMIN_PANEL_BUTT

logger_keyboards = logging.getLogger(__name__)


class KeyBoards:

    @staticmethod
    def kb_game():
        pass


kb_admin = create_inline_kb(2, **ADMIN_PANEL_BUTT, cancel_butt=False)
kb_back = create_inline_kb(width=1, back='Назад', cancel_butt=False)
kb_quiz = create_inline_kb(start_quiz='Начать', cancel_butt=False)
