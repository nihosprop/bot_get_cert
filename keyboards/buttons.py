import logging

logger_buttons = logging.getLogger(__name__)

ADMIN_PANEL_BUTT: dict[str, str] = {
        'newsletter': 'Рассылка',
        'replace_text': 'Сопутствующий текст',
        'exit': 'Выход'}

BUTT_MENU: dict[str, str] = {}
BUTT_CANCEL: dict[str, str] = {'cancel': '❌ОТМЕНА'}
BUTT_BACK: dict[str, str] = {'back': 'Назад'}

BUTT_SEX: dict[str, str] = {'male': 'Мужской', 'female': 'Женский'}
