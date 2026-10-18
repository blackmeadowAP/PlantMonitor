"""Пользователи и коды-приглашения."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, Text, true
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base
from core.models.enums import UserRole
from core.models.types import BigIntPK, CreatedAt, pg_enum, tz

user_role_enum = pg_enum(UserRole, "user_role")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        # Работник и агроном привязаны к предприятию, суперпользователь — к области
        CheckConstraint(
            "role NOT IN ('worker', 'agronomist') OR org_id IS NOT NULL", name="org_required"
        ),
        CheckConstraint("role <> 'superuser' OR region_id IS NOT NULL", name="region_required"),
    )

    id: Mapped[BigIntPK]
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(Text)
    role: Mapped[UserRole] = mapped_column(user_role_enum)
    org_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id"))
    region_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("regions.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true())
    consent_at: Mapped[datetime | None] = mapped_column(tz())
    created_at: Mapped[CreatedAt]


class Invite(Base):
    __tablename__ = "invites"

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    role: Mapped[UserRole] = mapped_column(user_role_enum)
    org_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id"))
    region_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("regions.id"))
    # null — код создан скриптом (seed / консоль администратора), а не пользователем
    created_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    expires_at: Mapped[datetime] = mapped_column(tz())
    used_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    used_at: Mapped[datetime | None] = mapped_column(tz())
