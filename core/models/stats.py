"""Аналитика: дневные показатели и отчёты."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, Numeric, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base
from core.models.enums import Trend
from core.models.types import BigIntPK, CreatedAt, pg_enum, tz


class DailyFieldStats(Base):
    __tablename__ = "daily_field_stats"

    field_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("fields.id"), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    prevalence_pct: Mapped[Decimal | None] = mapped_column(Numeric)
    severity_avg: Mapped[Decimal | None] = mapped_column(Numeric)
    speed_pp_day: Mapped[Decimal | None] = mapped_column(Numeric)
    trend: Mapped[Trend | None] = mapped_column(pg_enum(Trend, "trend"))
    n_observations: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    last_photo_at: Mapped[datetime | None] = mapped_column(tz())


class DailyUserStats(Base):
    __tablename__ = "daily_user_stats"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    tasks_total: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    tasks_done: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    photos: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    photos_ok: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    avg_distance_m: Mapped[Decimal | None] = mapped_column(Numeric)
    unplanned: Mapped[int] = mapped_column(Integer, server_default=text("0"))


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[BigIntPK]
    scope: Mapped[str] = mapped_column(Text)  # org | region
    scope_id: Mapped[int] = mapped_column(BigInteger)
    period_from: Mapped[date] = mapped_column(Date)
    period_to: Mapped[date] = mapped_column(Date)
    s3_key: Mapped[str] = mapped_column(Text)
    facts: Mapped[dict[str, Any]] = mapped_column(JSONB)
    llm_summary: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    facts_hash: Mapped[str] = mapped_column(Text)
    created_at: Mapped[CreatedAt]
