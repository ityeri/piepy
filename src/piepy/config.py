import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    bot_token: str


def get_config_from_env() -> Config:
    load_dotenv()

    return Config(
        os.getenv('BOT_TOKEN')
    )
