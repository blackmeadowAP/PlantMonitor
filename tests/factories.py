"""Тестовые данные для проверок прав: две области, предприятия, пользователи всех ролей."""

from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import geo
from core.models import (
    ControlPoint,
    District,
    Field,
    Observation,
    Organization,
    Region,
    Task,
    User,
    UserRole,
)
from scripts.seed import seed


@dataclass
class World:
    region: Region
    other_region: Region
    org: Organization
    org2: Organization  # та же область
    foreign_org: Organization  # другая область
    admin: User
    superuser: User
    foreign_superuser: User
    agronomist: User
    agronomist2: User
    worker: User
    worker2: User
    inactive_agronomist: User
    task: Task  # задание worker на точке org
    observation: Observation  # наблюдение worker на точке org


async def make_user(
    session: AsyncSession, tg_id: int, role: UserRole, *, org_id=None, region_id=None, active=True
) -> User:
    user = User(
        tg_id=tg_id,
        full_name=f"Пользователь {tg_id}",
        role=role,
        org_id=org_id,
        region_id=region_id,
        is_active=active,
    )
    session.add(user)
    await session.flush()
    return user


async def make_world(session: AsyncSession) -> World:
    await seed(session)
    region = await session.scalar(select(Region))
    org, org2 = (await session.scalars(select(Organization).order_by(Organization.id))).all()

    other_region = Region(name="Гомельская область")
    session.add(other_region)
    await session.flush()
    district = District(region_id=other_region.id, name="Гомельский район")
    session.add(district)
    await session.flush()
    foreign_org = Organization(
        name="КСУП «Чужое»", district_id=district.id, location=geo.point(52.44, 30.98)
    )
    session.add(foreign_org)
    await session.flush()

    worker = await make_user(session, 501, UserRole.worker, org_id=org.id)
    point = await session.scalar(
        select(ControlPoint).join(Field).where(Field.org_id == org.id).limit(1)
    )
    task = Task(point_id=point.id, user_id=worker.id, date=date.today())
    session.add(task)
    await session.flush()
    observation = Observation(
        task_id=task.id,
        point_id=point.id,
        user_id=worker.id,
        location=geo.point(53.83, 27.42),
        taken_at=datetime.now(UTC),
        plants_affected=0,
        wet_leaves=False,
        is_unplanned=False,
    )
    session.add(observation)
    await session.flush()

    return World(
        region=region,
        other_region=other_region,
        org=org,
        org2=org2,
        foreign_org=foreign_org,
        admin=await make_user(session, 100, UserRole.admin),
        superuser=await make_user(session, 200, UserRole.superuser, region_id=region.id),
        foreign_superuser=await make_user(
            session, 201, UserRole.superuser, region_id=other_region.id
        ),
        agronomist=await make_user(session, 300, UserRole.agronomist, org_id=org.id),
        agronomist2=await make_user(session, 301, UserRole.agronomist, org_id=org2.id),
        worker=worker,
        worker2=await make_user(session, 502, UserRole.worker, org_id=org.id),
        inactive_agronomist=await make_user(
            session, 302, UserRole.agronomist, org_id=org.id, active=False
        ),
        task=task,
        observation=observation,
    )
