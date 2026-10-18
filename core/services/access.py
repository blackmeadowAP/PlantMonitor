"""Права доступа (AGENTS.md, правило 8).

Агроном — только своё предприятие; суперпользователь — только своя область;
работник — только свои задания и фото; администратор — всё. Деактивированный — ничего.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import (
    ControlPoint,
    District,
    Field,
    Observation,
    Organization,
    Task,
    User,
    UserRole,
)


class AccessDenied(Exception):
    """Действие запрещено для пользователя."""


def is_active(user: User | None) -> bool:
    """Пользователь зарегистрирован и не деактивирован."""
    return user is not None and user.is_active


async def org_region_id(session: AsyncSession, org_id: int) -> int | None:
    """Область, в которой находится предприятие."""
    return await session.scalar(
        select(District.region_id)
        .join(Organization, Organization.district_id == District.id)
        .where(Organization.id == org_id)
    )


async def can_view_org(session: AsyncSession, user: User | None, org_id: int) -> bool:
    """Данные предприятия целиком (поля, точки, разметка, отчёты). Работнику — нет."""
    if not is_active(user):
        return False
    match user.role:
        case UserRole.admin:
            return True
        case UserRole.agronomist:
            return user.org_id == org_id
        case UserRole.superuser:
            return await org_region_id(session, org_id) == user.region_id
        case _:
            return False


def can_view_region(user: User | None, region_id: int) -> bool:
    """Сводные данные области."""
    if not is_active(user):
        return False
    if user.role == UserRole.admin:
        return True
    return user.role == UserRole.superuser and user.region_id == region_id


async def point_org_id(session: AsyncSession, point_id: int) -> int | None:
    """Предприятие, которому принадлежит контрольная точка."""
    return await session.scalar(
        select(Field.org_id)
        .join(ControlPoint, ControlPoint.field_id == Field.id)
        .where(ControlPoint.id == point_id)
    )


async def can_view_task(session: AsyncSession, user: User | None, task: Task) -> bool:
    """Задание: работнику — только своё, остальным — по предприятию точки."""
    if not is_active(user):
        return False
    if user.role == UserRole.worker:
        return task.user_id == user.id
    org_id = await point_org_id(session, task.point_id)
    return org_id is not None and await can_view_org(session, user, org_id)


async def can_view_observation(
    session: AsyncSession, user: User | None, observation: Observation
) -> bool:
    """Наблюдение и его фото: работнику — только свои, остальным — по предприятию автора."""
    if not is_active(user):
        return False
    if user.role == UserRole.worker:
        return observation.user_id == user.id
    # Внеплановое наблюдение может быть без точки — берём предприятие автора
    if observation.point_id is not None:
        org_id = await point_org_id(session, observation.point_id)
    else:
        org_id = await session.scalar(select(User.org_id).where(User.id == observation.user_id))
    return org_id is not None and await can_view_org(session, user, org_id)


async def can_create_invite(
    session: AsyncSession,
    user: User | None,
    role: UserRole,
    *,
    org_id: int | None = None,
    region_id: int | None = None,
) -> bool:
    """Кто кого приглашает: админ → суперпользователя, суперпользователь → агронома
    своей области, агроном → работника своего предприятия."""
    if not is_active(user):
        return False
    match (user.role, role):
        case (UserRole.admin, UserRole.superuser):
            return region_id is not None
        case (UserRole.superuser, UserRole.agronomist):
            return org_id is not None and await org_region_id(session, org_id) == user.region_id
        case (UserRole.agronomist, UserRole.worker):
            return org_id is not None and org_id == user.org_id
        case _:
            return False
