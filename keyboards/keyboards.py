import logging

from keyboards.kb_utils import create_inline_kb
from keyboards.buttons import (ADMIN_PANEL_BUTT,
    BUTT_GENDER,
    BUTT_COURSES,
    BUTT_DONE,
    BUTT_START,
    BUTTS_URL_PROMO,
    BUTTS_PROMO_OTHER_AUTHOR,
    BUTTS_URL_DZERANOV_PROMOCODES,
    BUTT_WANT_PROMOCODE_DZERANOV,
    BUTTS_URL_PRAGMATIC_PROGER)

logger_keyboards = logging.getLogger(__name__)


class KeyBoards:
    pass


kb_create_promo = create_inline_kb(
    width=1, url_buttons=BUTTS_URL_PROMO, cancel_butt=True,
    **BUTTS_PROMO_OTHER_AUTHOR)

kb_dzeranov_promocodes = create_inline_kb(url_buttons=BUTTS_URL_DZERANOV_PROMOCODES,
                                          exit=True,
                                          back=True,
                                          cancel_butt=False,
                                          **BUTT_WANT_PROMOCODE_DZERANOV)
kb_pragmatic_proger_promocodes = create_inline_kb(
    url_buttons=BUTTS_URL_PRAGMATIC_PROGER,
    exit=True,
    back=True,
    cancel_butt=False)

kb_butt_quiz = create_inline_kb(
    1, **BUTT_START,
    cancel_butt=False)

kb_butt_cancel = create_inline_kb(cancel_butt=True)

kb_admin = create_inline_kb(2, **ADMIN_PANEL_BUTT, cancel_butt=False)
kb_select_gender = create_inline_kb(2, **BUTT_GENDER, back=True)

def get_kb_courses():
    return create_inline_kb(**BUTT_COURSES, back=True)

kb_back_cancel = create_inline_kb(2, back=True, cancel_butt=True)
kb_end_quiz = create_inline_kb(**BUTT_DONE, cancel_butt=True, back=True)
kb_done_newsletter = create_inline_kb(**BUTT_DONE, cancel_butt=True)
kb_exit_back = create_inline_kb(exit=True, back=True, cancel_butt=False)