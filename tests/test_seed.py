"""Seed и создание администратора."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core import geo
from core.models import (
    ControlPoint,
    Crop,
    Disease,
    District,
    Field,
    Invite,
    Organization,
    Region,
    Task,
    User,
    UserRole,
)
from core.services.invites import INVITE_ALPHABET, INVITE_LENGTH
from scripts.create_admin import create_admin
from scripts.seed import seed

pytestmark = pytest.mark.db


async def count(session: AsyncSession, model: type) -> int:
    return await session.scalar(select(func.count()).select_from(model))


async def test_seed_counts(session: AsyncSession) -> None:
    await seed(session)
    assert await count(session, Region) == 1
    assert await count(session, District) == 2
    assert await count(session, Organization) == 2
    assert await count(session, Field) == 6
    assert await count(session, ControlPoint) == 30
    assert await count(session, Crop) == 3
    assert await count(session, Disease) == 8


async def test_seed_invites(session: AsyncSession) -> None:
    result = await seed(session)
    invites = (await session.scalars(select(Invite))).all()
    # Суперпользователь на область + агроном и работник на каждое предприятие
    assert len(invites) == len(result.codes) == 5
    assert {i.role for i in invites} == {UserRole.superuser, UserRole.agronomist, UserRole.worker}
    for invite in invites:
        assert len(invite.code) == INVITE_LENGTH
        assert set(invite.code) <= set(INVITE_ALPHABET)
        assert invite.used_by is None
        ttl = invite.expires_at - datetime.now(UTC)
        assert timedelta(days=6, hours=23) < ttl <= timedelta(days=7)
        if invite.role == UserRole.superuser:
            assert invite.region_id is not None
        else:
            assert invite.org_id is not None


async def test_seed_points_inside_fields(session: AsyncSession) -> None:
    await seed(session)
    outside = await session.scalar(
        select(func.count())
        .select_from(ControlPoint)
        .join(Field, Field.id == ControlPoint.field_id)
        .where(~func.ST_Covers(Field.boundary, ControlPoint.location))
    )
    assert outside == 0


async def test_distance_to_control_point_30m(session: AsyncSession) -> None:
    """Ключевой запрос docs/03: точка в 30 м от контрольной → ST_Distance ≈ 30."""
    await seed(session)
    cp = await session.scalar(select(ControlPoint).limit(1))
    as_geometry = func.ST_GeomFromWKB(func.ST_AsBinary(ControlPoint.location))
    cp_lat, cp_lon = (
        await session.execute(
            select(func.ST_Y(as_geometry), func.ST_X(as_geometry)).where(ControlPoint.id == cp.id)
        )
    ).one()
    lat, lon = geo.offset(cp_lat, cp_lon, north_m=30, east_m=0)
    distance = await session.scalar(
        text(
            "SELECT ST_Distance(location, ST_MakePoint(:lon, :lat)::geography) "
            "FROM control_points WHERE id = :point_id"
        ),
        {"lon": lon, "lat": lat, "point_id": cp.id},
    )
    assert float(distance) == pytest.approx(30, abs=0.5)


async def test_create_admin_new_and_existing(session: AsyncSession) -> None:
    admin = await create_admin(session, tg_id=1001, full_name="Админ")
    assert admin.role == UserRole.admin

    region = Region(name="Тест")
    session.add(region)
    await session.flush()
    user = User(tg_id=1002, full_name="Был", role=UserRole.superuser, region_id=region.id)
    user.is_active = False
    session.add(user)
    await session.flush()
    promoted = await create_admin(session, tg_id=1002, full_name="Был")
    assert promoted.id == user.id
    assert promoted.role == UserRole.admin
    assert promoted.is_active is True


@pytest.mark.parametrize("role", [UserRole.worker, UserRole.agronomist, UserRole.superuser])
async def test_user_role_requires_scope(session: AsyncSession, role: UserRole) -> None:
    """Работник/агроном без предприятия и суперпользователь без области запрещены (CHECK)."""
    session.add(User(tg_id=2000, full_name="X", role=role))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_task_unique_per_point_and_day(session: AsyncSession) -> None:
    await seed(session)
    cp = await session.scalar(select(ControlPoint).limit(1))
    org_id = await session.scalar(select(Field.org_id).where(Field.id == cp.field_id))
    worker = User(tg_id=3000, full_name="Работник", role=UserRole.worker, org_id=org_id)
    session.add(worker)
    await session.flush()
    day = datetime.now(UTC).date()
    session.add(Task(point_id=cp.id, user_id=worker.id, date=day))
    await session.flush()
    session.add(Task(point_id=cp.id, user_id=worker.id, date=day))
    with pytest.raises(IntegrityError):
        await session.flush()
