from dataclasses import dataclass

from environs import Env


@dataclass
class TgBot:
    token: str
    id_admin: str


@dataclass
class Config:
    tg_bot: TgBot
    redis_host: str


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    redis_host = env.str("REDIS_HOST", "localhost")  # По умолчанию "localhost"
    return Config(tg_bot=TgBot(token=env('BOT_TOKEN'), id_admin=env('ID_ADMIN')),
                  redis_host=redis_host)
