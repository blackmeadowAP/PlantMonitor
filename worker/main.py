"""Фоновый обработчик arq: arq worker.main.WorkerSettings.

Задачи (обработка фото, показатели, отчёты) добавляются на следующих шагах.
"""

import logging
from typing import Any, ClassVar

from arq.connections import RedisSettings

from core.config import get_settings
from core.logging import setup_logging

logger = logging.getLogger(__name__)


async def ping(ctx: dict[str, Any]) -> str:
    """Проверочная задача: очередь и worker работают."""
    return "pong"


async def startup(ctx: dict[str, Any]) -> None:
    """Инициализация worker."""
    setup_logging(get_settings().log_level)
    # У arq свой обработчик логов — не дублируем его записи в корневом логгере
    logging.getLogger("arq").propagate = False
    logger.info("Worker запущен")


class WorkerSettings:
    """Настройки arq-worker."""

    functions: ClassVar = [ping]
    on_startup = startup
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
