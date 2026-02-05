from __future__ import annotations

from src.bot import OptionsBot
from src.schemas import load_alpaca_env, load_settings, load_telegram_env
from src.utils import setup_logger

if __name__ == "__main__":
    setup_logger()
    settings = load_settings()
    OptionsBot(settings, load_alpaca_env(), load_telegram_env()).run()
