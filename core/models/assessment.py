"""Разметка, подсказки ИИ, очаги, обработки."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    false,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base
from core.models.enums import FocusStatus, Verdict
from core.models.types import BigIntPK, CreatedAt, pg_enum, point_type, tz


class AIPrediction(Base):
    __tablename__ = "ai_predictions"

    id: Mapped[BigIntPK]
    photo_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("photos.id"), index=True)
    model_version: Mapped[str] = mapped_column(Text)
    top1_disease_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("diseases.id"))
    top1_label: Mapped[str] = mapped_column(Text)
    top1_prob: Mapped[float] = mapped_column(Float)
    top3: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    created_at: Mapped[CreatedAt]


class Assessment(Base):
    """Оценка агронома. Действующая — последняя по observation_id."""

    __tablename__ = "assessments"

    id: Mapped[BigIntPK]
    observation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("observations.id"))
    agronomist_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    verdict: Mapped[Verdict] = mapped_column(pg_enum(Verdict, "verdict"))
    disease_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("diseases.id"))
    severity: Mapped[int | None] = mapped_column(Integer)
    confirmed_on_site: Mapped[bool] = mapped_column(Boolean, server_default=false())
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[CreatedAt]


# Поиск действующей (последней) оценки наблюдения
Index(
    "ix_assessments_observation_id_created_at",
    Assessment.observation_id,
    Assessment.created_at.desc(),
)


class Focus(Base):
    """Очаг болезни."""

    __tablename__ = "foci"
    __table_args__ = (Index("ix_foci_field_id_status", "field_id", "status"),)

    id: Mapped[BigIntPK]
    field_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("fields.id"))
    disease_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("diseases.id"))
    point_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("control_points.id"))
    location: Mapped[str] = mapped_column(point_type())
    area_ha: Mapped[Decimal | None] = mapped_column(Numeric)
    status: Mapped[FocusStatus] = mapped_column(pg_enum(FocusStatus, "focus_status"))
    detected_at: Mapped[datetime] = mapped_column(tz())
    closed_at: Mapped[datetime | None] = mapped_column(tz())
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))


class FocusUpdate(Base):
    __tablename__ = "focus_updates"

    id: Mapped[BigIntPK]
    focus_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("foci.id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    prevalence_pct: Mapped[Decimal] = mapped_column(Numeric)
    severity: Mapped[Decimal | None] = mapped_column(Numeric)
    note: Mapped[str | None] = mapped_column(Text)


class Treatment(Base):
    __tablename__ = "treatments"

    id: Mapped[BigIntPK]
    field_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("fields.id"), index=True)
    focus_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("foci.id"))
    date: Mapped[date] = mapped_column(Date)
    product: Mapped[str] = mapped_column(Text)
    rate: Mapped[str] = mapped_column(Text)
    area_ha: Mapped[Decimal] = mapped_column(Numeric)
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
