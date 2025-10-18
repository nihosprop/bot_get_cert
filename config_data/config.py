from dataclasses import dataclass

from environs import Env


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
    log_tg_cert_enabled: bool
    log_tg_cert_chat_id: int | None
    log_tg_cert_thread_id: int | None
    log_error_tg_enabled: bool
    log_error_tg_chat_id: int | None
    log_error_tg_thread_id: int | None


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    redis_host = env.str("REDIS_HOST", "localhost")
    stepik_client_id = env('STEPIK_CLIENT_ID')
    stepik_client_secret = env('STEPIK_CLIENT_CECRET')
    level_log = env.str('LOG_LEVEL', 'INFO')
    w_text = env.bool('W_TEXT_ENABLED', False)
    log_tg_cert_enabled = env.bool('LOG_TG_CERT_ENABLED', False)
    log_tg_cert_chat_id = env.int('LOG_TG_CERT_CHAT_ID', None)
    log_tg_cert_thread_id = env.int('LOG_TG_CERT_THREAD_ID', None)
    log_error_tg_enabled = env.bool('LOG_ERROR_TG_ENABLED', False)
    log_error_tg_chat_id = env.int('LOG_ERROR_TG_CHAT_ID', None)
    log_error_tg_thread_id = env.int('LOG_ERROR_TG_THREAD_ID', None)
    
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
        log_tg_cert_enabled=log_tg_cert_enabled,
        log_tg_cert_chat_id=log_tg_cert_chat_id,
        log_tg_cert_thread_id=log_tg_cert_thread_id,
        log_error_tg_enabled=log_error_tg_enabled,
        log_error_tg_chat_id=log_error_tg_chat_id,
        log_error_tg_thread_id=log_error_tg_thread_id)
