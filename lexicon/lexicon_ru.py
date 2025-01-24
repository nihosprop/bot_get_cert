from dataclasses import dataclass
import logging

logger_lexicon = logging.getLogger(__name__)


@dataclass
class LexiconCommandsRu:
    start: str = 'Запуск'
    admin: str = 'Админ панель'


@dataclass
class LexiconRu:
    await_start = ('<b>Что-бы запустить бота нажмите:\n'
                   '-> /start</b>')
    text_adm_panel: str = '<code>💻 Админ панель 💻</code>'
    text_antispam: str = ('Бот оборудован анти-спам фильтром.\nЧастая '
                          'бессмысленная отправка сообщений игнорируется.')
    text_survey: str = ('Для получения сертификата заполните анкету.\n'
                        'Следуйте примерам ввода данных, там где они есть,'
                        ' иначе не корректные сообщения будут игнорироваться.\n'
                        'Для получения скидки перейдите в соответсвующий '
                        'раздел.')
    text_sent_fullname: str = ('Отправьте ваши Имя и Фамилию.\n'
                               'Пример:\n<code>Иван Иванов</code>')
    text_gender: str = 'Имя и Фамилия записаны✅\nВыберите ваш пол:'
    text_select_course: str = 'Ваш пол записан✅\nВыберите пройденный курс:'
    text_course_number_done: str = ('Номер курса записан✅\nОтправьте '
                                    'примерную дату '
                                    'отзыва.\nПример: 07.07.2024')
    text_data_done: str = ('Дата записана✅\nПришлите ссылку на ваш'
                           ' профиль Stepik.\n'
                           'Ссылку можно получить:\n\n'
                           '1. Из браузера:\n'
                           'Нажать на свой аватар в Stepik -> Профиль ->'
                           ' скопировать ссылку.\n\n'
                           '2. Из приложения:\n'
                           'Нажать поделиться -> скопировать ссылку, либо сразу'
                           ' поделиться переслав боту.\n\n'
                           'Примеры ссылок:\n'
                           'https://stepik.org/users/27217717/profile\n\n'
                           'https://stepik.org/users/27217717')
