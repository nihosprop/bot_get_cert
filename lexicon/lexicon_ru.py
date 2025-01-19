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
    text_survey: str = 'Подайте заявку, заполнив анкету.'
    text_sent_fullname: str = ('Отправьте ваши Имя и Фамилию.\n'
                               'Пример:\n<code>Питон '
                               'Джаваскриптович</code>')
