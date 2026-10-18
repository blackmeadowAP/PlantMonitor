"""Коды-приглашения и регистрация (ОБ-1)."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Invite, UserRole
from core.services import invites, users
from core.services.access import AccessDenied
from core.services.invites import InviteError, InviteProblem
from tests.factories import World, make_world

pytestmark = pytest.mark.db


@pytest.fixture
async def world(session: AsyncSession) -> World:
    return await make_world(session)


async def test_agronomist_invites_worker(session: AsyncSession, world: World) -> None:
    invite = await invites.create_invite(
        session, world.agronomist, UserRole.worker, org_id=world.org.id
    )
    assert invite.created_by == world.agronomist.id
    assert invite.org_id == world.org.id
    assert invite.expires_at - datetime.now(UTC) > timedelta(days=6, hours=23)


async def test_create_invite_denied(session: AsyncSession, world: World) -> None:
    with pytest.raises(AccessDenied):
        await invites.create_invite(
            session, world.agronomist, UserRole.worker, org_id=world.org2.id
        )
    with pytest.raises(AccessDenied):
        await invites.create_invite(
            session, world.superuser, UserRole.agronomist, org_id=world.foreign_org.id
        )


async def test_register_by_code(session: AsyncSession, world: World) -> None:
    invite = await invites.create_invite(
        session, world.superuser, UserRole.agronomist, org_id=world.org2.id
    )
    user = await users.register(session, 9001, invite.code.lower(), "Петров Пётр")
    assert user.role == UserRole.agronomist
    assert user.org_id == world.org2.id
    assert user.consent_at is not None
    assert invite.used_by == user.id
    assert invite.used_at is not None


async def test_code_works_only_once(session: AsyncSession, world: World) -> None:
    invite = await invites.create_invite(
        session, world.agronomist, UserRole.worker, org_id=world.org.id
    )
    await users.register(session, 9002, invite.code, "Сидоров Сидор")
    with pytest.raises(InviteError) as e:
        await users.register(session, 9003, invite.code, "Другой Человек")
    assert e.value.problem == InviteProblem.used


async def test_expired_code(session: AsyncSession, world: World) -> None:
    session.add(
        Invite(
            code="EXPIRED2",
            role=UserRole.worker,
            org_id=world.org.id,
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
    )
    await session.flush()
    with pytest.raises(InviteError) as e:
        await users.register(session, 9004, "EXPIRED2", "Иванов Иван")
    assert e.value.problem == InviteProblem.expired


async def test_unknown_code(session: AsyncSession) -> None:
    with pytest.raises(InviteError) as e:
        await invites.get_valid_invite(session, "NOSUCH22")
    assert e.value.problem == InviteProblem.not_found


async def test_registered_account_cannot_register_again(
    session: AsyncSession, world: World
) -> None:
    invite = await invites.create_invite(
        session, world.agronomist, UserRole.worker, org_id=world.org.id
    )
    with pytest.raises(users.AlreadyRegistered):
        await users.register(session, world.worker.tg_id, invite.code, "Повтор Повторов")
    assert invite.used_by is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Иванов Иван", "Иванов Иван"),
        ("  Иванов   Иван  Иванович ", "Иванов Иван Иванович"),
        ("Иван", None),
        ("Иванов 123", None),
        ("/start ABC", None),
        ("а" * 60 + " " + "б" * 60, None),
    ],
)
def test_clean_full_name(raw: str, expected: str | None) -> None:
    assert users.clean_full_name(raw) == expected
