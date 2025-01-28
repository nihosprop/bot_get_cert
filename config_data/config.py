from dataclasses import dataclass

from environs import Env


@dataclass
class TgBot:
    token: str
    id_admins: str


@dataclass
class Stepik:
    client_id: str
    client_cecret: str


@dataclass
class Config:
    tg_bot: TgBot
    redis_host: str
    stepik: Stepik


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    redis_host = env.str("REDIS_HOST", "localhost")  # По умолчанию "localhost"
    stepik_client_id = env('STEPIK_CLIENT_ID')
    stepik_client_cecret = env('STEPIK_CLIENT_CECRET')
    return Config(tg_bot=TgBot(token=env('BOT_TOKEN'), id_admins=env('ID_ADMIN')),
                  stepik=Stepik(client_id=stepik_client_id,
                                client_cecret=stepik_client_cecret),
                  redis_host=redis_host)
