"""Территория: списки для выбора в боте с учётом прав."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import District, Organization, Region, User, UserRole


async def list_regions(session: AsyncSession) -> Sequence[Region]:
    """Все области (для администратора)."""
    return (await session.scalars(select(Region).order_by(Region.name))).all()


async def list_orgs_for(session: AsyncSession, user: User) -> Sequence[Organization]:
    """Предприятия, доступные пользователю: суперпользователю — своей области."""
    query = select(Organization).order_by(Organization.name)
    if user.role == UserRole.superuser:
        query = query.join(District).where(District.region_id == user.region_id)
    elif user.role != UserRole.admin:
        query = query.where(Organization.id == user.org_id)
    return (await session.scalars(query)).all()
