import logging

logger_buttons = logging.getLogger(__name__)

ADMIN_PANEL_BUTT: dict[str, str] = {
    'newsletter': 'Рассылка',
    'certs_data': 'Данные по сертификатам',
    'make_cert': 'Сделать сертификат',
    'add_admin': 'Добавить админа',
    'exit': 'Выход'}

BUTT_CANCEL: dict[str, str] = {'cancel': '❌ОТМЕНА'}
BUTT_BACK: dict[str, str] = {'back': '🔙 Назад'}
BUTT_DONE: dict[str, str] = {'done': 'Подтвердить✅'}

BUTT_NEWSLETTER: dict[str, str] = {}
BUTT_START: dict[str, str] = {
    'get_cert': 'Получить сертификат',
    'get_promo': 'Получить промокод со скидкой'}
BUTT_GENDER: dict[str, str] = {'male': 'Мужской ♂', 'female': 'Женский ♀'}
BUTT_COURSES: dict[str, str] = {
    'id_1_214271': 'Лучший по Python.Часть 1',
    'id_2_221885': 'Лучший по Python.Часть 2',
    'id_3_227627': 'Лучший по Python.Часть 3',
    'id_4_241971': 'Лучший по Python.Часть 4',
    'id_5_252829': 'Основы Git и GitHub'}

BUTTS_URL_PROMO: dict[str, str] = {
    'Лучший по Python.Часть 3':
        'https://stepik.org/a/227627/pay?promo=90e83ebae76d239a',
    'Лучший по Python. Часть 4':
        'https://stepik.org/a/241971/pay?promo=c9af0a0dae2667f9'}
BUTTS_PROMO_OTHER_AUTHOR: dict[str, str] = {
    'courses_joseph_dzeranov': 'Курсы Иосифа Дзеранова',
    'courses_pragmatic_programmer': 'Курсы Pragmatic Programmer'
    }
