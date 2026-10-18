"""Коды-приглашения (ОБ-1): выдача, проверка, использование."""

import enum
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Invite, User, UserRole
from core.services.access import AccessDenied, can_create_invite

INVITE_TTL_DAYS = 7
# Без похожих символов (0/O, 1/I/L), чтобы код можно было продиктовать
INVITE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
INVITE_LENGTH = 8


class InviteProblem(enum.StrEnum):
    """Почему код нельзя использовать."""

    not_found = "not_found"
    used = "used"
    expired = "expired"


class InviteError(Exception):
    """Код недействителен."""

    def __init__(self, problem: InviteProblem) -> None:
        super().__init__(problem.value)
        self.problem = problem


def generate_invite_code() -> str:
    """Случайный код для /start <код> (допустим в deep link Telegram)."""
    return "".join(secrets.choice(INVITE_ALPHABET) for _ in range(INVITE_LENGTH))


def normalize_code(code: str) -> str:
    """Код из сообщения: без пробелов, в верхнем регистре."""
    return code.strip().upper()


def invite_expires_at(now: datetime | None = None) -> datetime:
    """Момент истечения кода, созданного сейчас (UTC)."""
    return (now or datetime.now(UTC)) + timedelta(days=INVITE_TTL_DAYS)


async def create_invite(
    session: AsyncSession,
    creator: User,
    role: UserRole,
    *,
    org_id: int | None = None,
    region_id: int | None = None,
) -> Invite:
    """Выдаёт код с проверкой прав. Коммит — на вызывающей стороне."""
    if not await can_create_invite(session, creator, role, org_id=org_id, region_id=region_id):
        raise AccessDenied(f"{creator.role} не может пригласить {role}")
    invite = Invite(
        code=generate_invite_code(),
        role=role,
        org_id=org_id,
        region_id=region_id,
        created_by=creator.id,
        expires_at=invite_expires_at(),
    )
    session.add(invite)
    await session.flush()
    return invite


async def get_valid_invite(
    session: AsyncSession, code: str, *, for_update: bool = False, now: datetime | None = None
) -> Invite:
    """Код существует, не использован и не истёк — иначе InviteError."""
    query = select(Invite).where(Invite.code == normalize_code(code))
    if for_update:
        query = query.with_for_update()
    invite = await session.scalar(query)
    if invite is None:
        raise InviteError(InviteProblem.not_found)
    if invite.used_by is not None:
        raise InviteError(InviteProblem.used)
    if invite.expires_at <= (now or datetime.now(UTC)):
        raise InviteError(InviteProblem.expired)
    return invite
