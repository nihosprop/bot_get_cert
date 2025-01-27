import logging

logger_buttons = logging.getLogger(__name__)

ADMIN_PANEL_BUTT: dict[str, str] = {
        'newsletter': 'Рассылка',
        'replace_text': 'Сопутствующий текст',
        'exit': 'Выход'}

BUTT_CANCEL: dict[str, str] = {'cancel': '❌ОТМЕНА'}
BUTT_BACK: dict[str, str] = {'back': '🔙 Назад'}
BUTT_DONE: dict[str, str] = {'done': 'Подтвердить✅'}

BUTT_START: dict[str, str] = {
        'get_cert': 'Получить сертификат',
        'get_promo': 'Получить промокод со скидкой'}
BUTT_GENDER: dict[str, str] = {'male': 'Мужской ♂', 'female': 'Женский ♀'}
BUTT_COURSES: dict[str, str] = {
        'id_1_214271': 'Лучший по Python.Часть 1',
        'id_2_221885': 'Лучший по Python.Часть 2',
        'id_3': '🔜 Лучший по Python.Часть 3',
        'id_4': '🔜 Лучший по Python.Часть 4',
        'id_5': '🔜 Лучший по Python.Часть 5',
        'id_6': '🔜 Лучший по Python.ООП'}

BUTT_URL_PROMO: dict[str, str] = {
        'Лучший по Python.Часть 2':
        'https://stepik.org/a/221885/pay?promo=15f84e690c978074'}
