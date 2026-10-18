"""Настройка логирования."""

import logging

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def setup_logging(level: str = "INFO") -> None:
    """Единый формат логов для bot, api и worker."""
    logging.basicConfig(level=level.upper(), format=LOG_FORMAT, force=True)
    # httpx пишет полный URL запросов, а в URL Telegram API есть токен бота
    logging.getLogger("httpx").setLevel(logging.WARNING)
