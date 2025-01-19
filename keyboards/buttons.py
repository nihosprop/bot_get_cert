import logging

from lexicon import LexiconRu

logger_buttons = logging.getLogger(__name__)

ADMIN_PANEL_BUTT: dict[str, str] = {
        'newsletter': 'Рассылка',
        'exit': 'Выход'}

BUTT_MENU: dict[str, str] = {}
CANCEL_BUTT: dict[str, str] = {'cancel': '❌ОТМЕНА'}
