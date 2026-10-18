"""Поля и контрольные точки."""

from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, Numeric, Text, false, text, true
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base
from core.models.enums import PointKind
from core.models.types import BigIntPK, CreatedAt, pg_enum, point_type, polygon_type


class Field(Base):
    __tablename__ = "fields"

    id: Mapped[BigIntPK]
    org_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(Text)
    crop_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("crops.id"))
    area_ha: Mapped[Decimal] = mapped_column(Numeric)
    boundary: Mapped[str | None] = mapped_column(polygon_type())
    centroid: Mapped[str] = mapped_column(point_type())
    growth_stage: Mapped[str | None] = mapped_column(Text)
    daily_mode: Mapped[bool] = mapped_column(Boolean, server_default=false())
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true())


class ControlPoint(Base):
    __tablename__ = "control_points"

    id: Mapped[BigIntPK]
    field_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("fields.id"), index=True)
    location: Mapped[str] = mapped_column(point_type())
    kind: Mapped[PointKind] = mapped_column(pg_enum(PointKind, "point_kind"))
    assigned_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), index=True
    )
    interval_days: Mapped[int] = mapped_column(Integer, server_default=text("3"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true())
    created_at: Mapped[CreatedAt]
