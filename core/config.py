"""Настройки приложения из переменных окружения (pydantic-settings)."""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Пороги аналитики (docs/06). Изменения фиксировать в docs/10_DECISIONS.md.
TREND_THRESHOLD_PP_PER_DAY = 0.5
PREVALENCE_WINDOW_DAYS = 3
SPEED_WINDOW_DAYS = 7


class Settings(BaseSettings):
    """Все настройки сервиса. Секреты — только через окружение / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    # Telegram
    bot_token: SecretStr = SecretStr("")
    archive_channel_id: int | None = None

    # Общие
    log_level: str = "INFO"
    tz_name: str = "Europe/Minsk"

    # Хранилища
    database_url: str = "postgresql+asyncpg://agro:agro@localhost:5432/agro"
    redis_url: str = "redis://localhost:6379/0"

    # S3
    s3_endpoint_url: str | None = "http://localhost:9000"
    s3_access_key: SecretStr = SecretStr("")
    s3_secret_key: SecretStr = SecretStr("")
    s3_bucket: str = "agro"
    s3_region: str = "us-east-1"

    # Фото
    geo_max_distance_m: float = 50.0
    photo_max_side_px: int = 1600
    healthy_photo_retention_days: int = 30

    # Нейросеть
    ml_mode: Literal["off", "local", "space"] = "off"
    ml_confidence_threshold: float = 0.6
    hf_token: SecretStr = SecretStr("")

    # Языковая модель
    llm_enabled: bool = False
    llm_url: str = "http://ollama:11434/v1"
    llm_model: str = ""


@lru_cache
def get_settings() -> Settings:
    """Возвращает единый экземпляр настроек."""
    return Settings()
