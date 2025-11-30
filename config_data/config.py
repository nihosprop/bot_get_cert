import yaml
from dataclasses import dataclass, field
from environs import Env

@dataclass
class Course:
    name: str
    templates: dict[str, str]

@dataclass
class CourseData:
    courses: dict[int, Course]
    best_in_python_courses: list[int] = field(default_factory=list)


@dataclass
class TgBot:
    token: str
    id_admins: str


@dataclass
class Stepik:
    client_id: str
    client_secret: str


@dataclass
class Config:
    tg_bot: TgBot
    redis_host: str
    stepik: Stepik
    level_log: str
    w_text: bool
    tg_target_channel: int | None
    pragmatic_target_channel: int | None
    log_tg_cert_enabled: bool
    log_tg_cert_chat_id: int | None
    log_tg_cert_thread_id: int | None
    log_error_tg_enabled: bool
    log_error_tg_chat_id: int | None
    log_error_tg_thread_id: int | None
    pragmatic_courses: str | None
    courses_data: CourseData


def load_courses_from_yaml(path: str = 'config.yaml') -> CourseData:
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    courses_data = data.get('courses', {})
    courses = {}
    for course_id, course_info in courses_data.items():
        courses[int(course_id)] = Course(
            name=course_info['name'],
            templates=course_info['templates']
            )
    courses_data = CourseData(
        courses=courses,
        best_in_python_courses=data.get('best_in_python_courses', []))

    return courses_data


def load_config(path: str | None = None) -> Config:
    """
    Load configuration from environment variables and yaml file.

    Args: path (str | None, optional): Path to the environment file.
    Returns: Config: Configuration object.
    """
    env = Env()
    env.read_env(path)
    redis_host = env.str("REDIS_HOST", "localhost")
    stepik_client_id = env('STEPIK_CLIENT_ID')
    stepik_client_secret = env('STEPIK_CLIENT_SECRET')
    level_log = env.str('LOG_LEVEL', 'INFO')

    w_text = env.bool('W_TEXT_ENABLED', False)

    tg_target_channel = env.int('TG_TARGET_CHANNEL', None)
    pragmatic_target_channel = env.int('PRAGMATIC_TARGET_CHANNEL', None)

    log_tg_cert_enabled = env.bool('LOG_TG_CERT_ENABLED', False)
    log_tg_cert_chat_id = env.int('LOG_TG_CERT_CHAT_ID', None)
    log_tg_cert_thread_id = env.int('LOG_TG_CERT_THREAD_ID', None)

    log_error_tg_enabled = env.bool('LOG_ERROR_TG_ENABLED', False)
    log_error_tg_chat_id = env.int('LOG_ERROR_TG_CHAT_ID', None)
    log_error_tg_thread_id = env.int('LOG_ERROR_TG_THREAD_ID', None)

    # TODO: transfer to config.yaml
    pragmatic_courses = env.str('PRAGMATIC_COURSES', None)

    courses_data = load_courses_from_yaml()


    tg_bot = TgBot(
        token=env('BOT_TOKEN'),
        id_admins=env('ID_ADMIN'))

    return Config(
        tg_bot=tg_bot,
        stepik=Stepik(
            client_id=stepik_client_id,
            client_secret=stepik_client_secret),
        redis_host=redis_host,
        level_log=level_log,
        w_text=w_text,
        tg_target_channel=tg_target_channel,
        pragmatic_target_channel=pragmatic_target_channel,
        log_tg_cert_enabled=log_tg_cert_enabled,
        log_tg_cert_chat_id=log_tg_cert_chat_id,
        log_tg_cert_thread_id=log_tg_cert_thread_id,
        log_error_tg_enabled=log_error_tg_enabled,
        log_error_tg_chat_id=log_error_tg_chat_id,
        log_error_tg_thread_id=log_error_tg_thread_id,
        pragmatic_courses=pragmatic_courses,
        courses_data=courses_data)
