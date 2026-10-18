"""Тестовые данные (docs/03, раздел Seed): python -m scripts.seed

1 область, 2 района, 2 предприятия, по 3 поля и 5 точек на поле, справочник культур и болезней,
коды-приглашения для каждой роли (печатаются в консоль).
"""

import asyncio
import math
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core import geo
from core.db import get_sessionmaker
from core.models import (
    ControlPoint,
    Crop,
    Disease,
    District,
    Field,
    Invite,
    Organization,
    PointKind,
    Region,
    UserRole,
)
from core.services.invites import generate_invite_code, invite_expires_at

SEVERITY_SCALE = {
    "max": 4,
    "labels": {"0": "нет", "1": "слабое", "2": "среднее", "3": "сильное", "4": "очень сильное"},
}

# Культура → [(болезнь, латинское название)]
CROPS: dict[str, list[tuple[str, str]]] = {
    "Картофель": [
        ("Фитофтороз", "Phytophthora infestans"),
        ("Альтернариоз", "Alternaria solani"),
    ],
    "Озимая пшеница": [
        ("Септориоз", "Zymoseptoria tritici"),
        ("Бурая ржавчина", "Puccinia triticina"),
        ("Мучнистая роса", "Blumeria graminis"),
        ("Фузариоз", "Fusarium spp."),
    ],
    "Рапс": [
        ("Склеротиниоз", "Sclerotinia sclerotiorum"),
        ("Альтернариоз", "Alternaria brassicae"),
    ],
}

REGION_NAME = "Минская область"
# (район, предприятие, широта, долгота)
ORGS = [
    ("Минский район", "СПК «Тестовый-1»", 53.83, 27.42),
    ("Смолевичский район", "ОАО «Тестовое-2»", 54.05, 28.10),
]
# (культура, название поля, площадь га, смещение центра от усадьбы на север/восток, м)
FIELDS = [
    ("Картофель", "Поле №1", 40, 1500, 0),
    ("Озимая пшеница", "Поле №2", 80, 0, 2000),
    ("Рапс", "Поле №3", 60, -1800, -500),
]
POINTS_PER_FIELD = 5


@dataclass
class SeedResult:
    """Созданные коды-приглашения: (роль, где действует, код)."""

    codes: list[tuple[UserRole, str, str]]


async def seed(session: AsyncSession) -> SeedResult:
    """Заполняет пустую БД тестовыми данными. Коммит — на вызывающей стороне."""
    region = Region(name=REGION_NAME)
    session.add(region)
    await session.flush()

    crops: dict[str, Crop] = {}
    for crop_name, diseases in CROPS.items():
        crop = Crop(name=crop_name)
        session.add(crop)
        await session.flush()
        crops[crop_name] = crop
        for name, latin in diseases:
            session.add(
                Disease(crop_id=crop.id, name=name, latin_name=latin, severity_scale=SEVERITY_SCALE)
            )

    result = SeedResult(codes=[])
    code = await _invite(session, UserRole.superuser, region_id=region.id)
    result.codes.append((UserRole.superuser, REGION_NAME, code))

    for district_name, org_name, lat, lon in ORGS:
        district = District(region_id=region.id, name=district_name)
        session.add(district)
        await session.flush()
        org = Organization(name=org_name, district_id=district.id, location=geo.point(lat, lon))
        session.add(org)
        await session.flush()
        for crop_name, field_name, area_ha, north_m, east_m in FIELDS:
            f_lat, f_lon = geo.offset(lat, lon, north_m, east_m)
            await _add_field(
                session, org.id, crops[crop_name].id, field_name, area_ha, f_lat, f_lon
            )
        for role in (UserRole.agronomist, UserRole.worker):
            code = await _invite(session, role, org_id=org.id)
            result.codes.append((role, org_name, code))

    await session.flush()
    return result


async def _add_field(
    session: AsyncSession,
    org_id: int,
    crop_id: int,
    name: str,
    area_ha: int,
    lat: float,
    lon: float,
) -> None:
    """Поле-квадрат заданной площади и 5 точек: центр и четыре точки по диагоналям."""
    side_m = math.sqrt(area_ha * 10_000)
    field = Field(
        org_id=org_id,
        name=name,
        crop_id=crop_id,
        area_ha=Decimal(area_ha),
        boundary=geo.square(lat, lon, side_m),
        centroid=geo.point(lat, lon),
    )
    session.add(field)
    await session.flush()
    q = side_m / 4
    offsets = [(0, 0), (q, q), (q, -q), (-q, q), (-q, -q)][:POINTS_PER_FIELD]
    for i, (north_m, east_m) in enumerate(offsets):
        p_lat, p_lon = geo.offset(lat, lon, north_m, east_m)
        session.add(
            ControlPoint(
                field_id=field.id,
                location=geo.point(p_lat, p_lon),
                # Одна точка риска на поле (низина у края) — для проверки приоритетов заданий
                kind=PointKind.risk if i == len(offsets) - 1 else PointKind.regular,
            )
        )


async def _invite(
    session: AsyncSession,
    role: UserRole,
    *,
    org_id: int | None = None,
    region_id: int | None = None,
) -> str:
    """Создаёт код-приглашение без автора (created_by = null)."""
    code = generate_invite_code()
    session.add(
        Invite(
            code=code, role=role, org_id=org_id, region_id=region_id, expires_at=invite_expires_at()
        )
    )
    return code


ROLE_TITLES = {
    UserRole.superuser: "Суперпользователь",
    UserRole.agronomist: "Агроном",
    UserRole.worker: "Работник",
}


async def main() -> None:
    """Запуск из консоли: заполняет БД, если она пуста, и печатает коды."""
    async with get_sessionmaker()() as session:
        if await session.scalar(select(func.count()).select_from(Region)):
            print("В БД уже есть данные — seed пропущен.")
            return
        result = await seed(session)
        await session.commit()
    print("Тестовые данные созданы. Коды-приглашения (действуют 7 дней):")
    for role, scope, code in result.codes:
        print(f"  {ROLE_TITLES[role]:<18} {scope:<20} /start {code}")


if __name__ == "__main__":
    asyncio.run(main())
