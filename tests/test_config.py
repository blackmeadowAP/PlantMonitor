"""Настройки из переменных окружения."""

import pytest

from core.config import Settings


def test_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ML_MODE", raising=False)
    monkeypatch.delenv("GEO_MAX_DISTANCE_M", raising=False)
    settings = Settings(_env_file=None)
    assert settings.ml_mode == "off"
    assert settings.geo_max_distance_m == 50
    assert settings.tz_name == "Europe/Minsk"
    assert settings.llm_enabled is False


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEO_MAX_DISTANCE_M", "30")
    monkeypatch.setenv("ML_MODE", "local")
    settings = Settings(_env_file=None)
    assert settings.geo_max_distance_m == 30
    assert settings.ml_mode == "local"


def test_secrets_hidden_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "123:secret-token")
    settings = Settings(_env_file=None)
    assert "secret-token" not in repr(settings)
    assert settings.bot_token.get_secret_value() == "123:secret-token"


def test_invalid_ml_mode_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ML_MODE", "cloud")
    with pytest.raises(ValueError):
        Settings(_env_file=None)


def test_empty_values_use_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Пустые строки из .env.example не ломают запуск."""
    monkeypatch.setenv("ARCHIVE_CHANNEL_ID", "")
    monkeypatch.setenv("GEO_MAX_DISTANCE_M", "")
    settings = Settings(_env_file=None)
    assert settings.archive_channel_id is None
    assert settings.geo_max_distance_m == 50


def test_telegram_api_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Бот ходит на адрес Bot API из TELEGRAM_API_URL (без сетевых запросов)."""
    from bot.app import create_bot

    monkeypatch.setenv("BOT_TOKEN", "42:TEST")
    monkeypatch.setenv("TELEGRAM_API_URL", "http://localhost:8081/")
    bot = create_bot(Settings(_env_file=None))
    assert bot.session.api.api_url("42:TEST", "getMe") == "http://localhost:8081/bot42:TEST/getMe"


def test_bot_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
    from bot.app import create_bot

    monkeypatch.delenv("BOT_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        create_bot(Settings(_env_file=None))
