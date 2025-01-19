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
BUTT_COURSES: dict[str, str] = {
        'course_1': 'Лучший по Python. Часть 1',
        'course_2': 'Лучший по Python. Часть 2',
        'course_3': 'Лучший по Python. Часть 3',
        'course_4': 'Лучший по Python. Часть 4',
        'course_5': 'Лучший по Python. Часть 5'}
