"""Права доступа (docs/09: core/services/access.py)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Observation, UserRole
from core.services import access
from tests.factories import World, make_world

pytestmark = pytest.mark.db


@pytest.fixture
async def world(session: AsyncSession) -> World:
    return await make_world(session)


# --- Агроном ↔ предприятия ---


async def test_agronomist_sees_own_org(session: AsyncSession, world: World) -> None:
    assert await access.can_view_org(session, world.agronomist, world.org.id)


async def test_agronomist_not_other_org(session: AsyncSession, world: World) -> None:
    assert not await access.can_view_org(session, world.agronomist, world.org2.id)
    assert not await access.can_view_org(session, world.agronomist, world.foreign_org.id)


async def test_agronomist_tasks_only_own_org(session: AsyncSession, world: World) -> None:
    assert await access.can_view_task(session, world.agronomist, world.task)
    assert not await access.can_view_task(session, world.agronomist2, world.task)
    assert not await access.can_view_observation(session, world.agronomist2, world.observation)


# --- Работник ↔ задания и фото ---


async def test_worker_sees_own_task_and_observation(session: AsyncSession, world: World) -> None:
    assert await access.can_view_task(session, world.worker, world.task)
    assert await access.can_view_observation(session, world.worker, world.observation)


async def test_worker_not_others_task(session: AsyncSession, world: World) -> None:
    """Даже коллега с того же предприятия не видит чужое задание и фото."""
    assert not await access.can_view_task(session, world.worker2, world.task)
    assert not await access.can_view_observation(session, world.worker2, world.observation)


async def test_worker_no_org_level_access(session: AsyncSession, world: World) -> None:
    assert not await access.can_view_org(session, world.worker, world.org.id)
    assert not access.can_view_region(world.worker, world.region.id)


# --- Суперпользователь ↔ области ---


async def test_superuser_sees_orgs_of_own_region(session: AsyncSession, world: World) -> None:
    assert await access.can_view_org(session, world.superuser, world.org.id)
    assert await access.can_view_org(session, world.superuser, world.org2.id)
    assert await access.can_view_task(session, world.superuser, world.task)
    assert access.can_view_region(world.superuser, world.region.id)


async def test_superuser_not_other_region(session: AsyncSession, world: World) -> None:
    assert not await access.can_view_org(session, world.superuser, world.foreign_org.id)
    assert not access.can_view_region(world.superuser, world.other_region.id)
    assert not await access.can_view_org(session, world.foreign_superuser, world.org.id)
    assert not await access.can_view_task(session, world.foreign_superuser, world.task)


async def test_unplanned_observation_uses_author_org(session: AsyncSession, world: World) -> None:
    """Внеплановое наблюдение без точки — доступ по предприятию автора."""
    unplanned = Observation(
        point_id=None,
        user_id=world.worker.id,
        location=world.observation.location,
        taken_at=world.observation.taken_at,
        plants_affected=1,
        wet_leaves=False,
        is_unplanned=True,
    )
    session.add(unplanned)
    await session.flush()
    assert await access.can_view_observation(session, world.agronomist, unplanned)
    assert not await access.can_view_observation(session, world.agronomist2, unplanned)
    assert not await access.can_view_observation(session, world.foreign_superuser, unplanned)


# --- Администратор и деактивированный пользователь ---


async def test_admin_sees_everything(session: AsyncSession, world: World) -> None:
    assert await access.can_view_org(session, world.admin, world.foreign_org.id)
    assert access.can_view_region(world.admin, world.other_region.id)
    assert await access.can_view_task(session, world.admin, world.task)


async def test_inactive_user_has_no_access(session: AsyncSession, world: World) -> None:
    user = world.inactive_agronomist
    assert not await access.can_view_org(session, user, world.org.id)
    assert not await access.can_view_task(session, user, world.task)
    assert not await access.can_view_observation(session, user, world.observation)
    assert not await access.can_create_invite(session, user, UserRole.worker, org_id=world.org.id)


async def test_deactivated_after_registration(session: AsyncSession, world: World) -> None:
    world.agronomist.is_active = False
    assert not await access.can_view_org(session, world.agronomist, world.org.id)


async def test_none_user_has_no_access(session: AsyncSession, world: World) -> None:
    assert not await access.can_view_org(session, None, world.org.id)
    assert not access.can_view_region(None, world.region.id)


# --- Кто кого приглашает ---


@pytest.mark.parametrize(
    ("creator", "role", "target", "allowed"),
    [
        ("admin", UserRole.superuser, "region", True),
        ("admin", UserRole.agronomist, "org", False),
        ("superuser", UserRole.agronomist, "org", True),
        ("superuser", UserRole.agronomist, "org2", True),
        ("superuser", UserRole.agronomist, "foreign_org", False),
        ("superuser", UserRole.superuser, "region", False),
        ("superuser", UserRole.worker, "org", False),
        ("agronomist", UserRole.worker, "org", True),
        ("agronomist", UserRole.worker, "org2", False),
        ("agronomist", UserRole.agronomist, "org", False),
        ("worker", UserRole.worker, "org", False),
    ],
)
async def test_can_create_invite(
    session: AsyncSession, world: World, creator: str, role: UserRole, target: str, allowed: bool
) -> None:
    target_obj = getattr(world, target)
    kwargs = {"region_id": target_obj.id} if target == "region" else {"org_id": target_obj.id}
    result = await access.can_create_invite(session, getattr(world, creator), role, **kwargs)
    assert result is allowed
