"""Создание администратора: python -m scripts.create_admin --tg-id 123456789 --name "Иван"

Если пользователь с таким tg_id уже есть — ему назначается роль admin.
"""

import argparse
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_sessionmaker
from core.models import User, UserRole


async def create_admin(session: AsyncSession, tg_id: int, full_name: str) -> User:
    """Создаёт или повышает пользователя до администратора. Коммит — на вызывающей стороне."""
    user = await session.scalar(select(User).where(User.tg_id == tg_id))
    if user is None:
        user = User(tg_id=tg_id, full_name=full_name, role=UserRole.admin)
        session.add(user)
    else:
        user.role = UserRole.admin
        user.is_active = True
    await session.flush()
    return user


async def main(tg_id: int, full_name: str) -> None:
    async with get_sessionmaker()() as session:
        user = await create_admin(session, tg_id, full_name)
        await session.commit()
    print(f"Администратор: id={user.id}, tg_id={user.tg_id}, имя={user.full_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Создать администратора")
    parser.add_argument(
        "--tg-id", type=int, required=True, help="Telegram ID (узнать у @userinfobot)"
    )
    parser.add_argument("--name", default="Администратор", help="Имя")
    args = parser.parse_args()
    asyncio.run(main(args.tg_id, args.name))
