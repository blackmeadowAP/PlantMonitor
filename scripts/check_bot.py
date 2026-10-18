"""Проверка связи с Telegram Bot API: python -m scripts.check_bot

Печатает имя бота по getMe. Токен в вывод не попадает.
"""

import asyncio

from bot.app import create_bot
from core.config import get_settings


async def main() -> None:
    settings = get_settings()
    bot = create_bot(settings)
    try:
        me = await bot.get_me()
    except Exception as e:
        raise SystemExit(f"Нет связи с {settings.telegram_api_url}: {type(e).__name__}") from None
    finally:
        await bot.session.close()
    print(f"Бот доступен: @{me.username} (id={me.id}), API: {settings.telegram_api_url}")


if __name__ == "__main__":
    asyncio.run(main())
