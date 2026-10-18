"""Коды-приглашения (ОБ-1): формат и срок действия."""

import secrets
from datetime import UTC, datetime, timedelta

INVITE_TTL_DAYS = 7
# Без похожих символов (0/O, 1/I/L), чтобы код можно было продиктовать
INVITE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
INVITE_LENGTH = 8


def generate_invite_code() -> str:
    """Случайный код для /start <код> (допустим в deep link Telegram)."""
    return "".join(secrets.choice(INVITE_ALPHABET) for _ in range(INVITE_LENGTH))


def invite_expires_at(now: datetime | None = None) -> datetime:
    """Момент истечения кода, созданного сейчас (UTC)."""
    return (now or datetime.now(UTC)) + timedelta(days=INVITE_TTL_DAYS)
