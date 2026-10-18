"""Сбор данных: задания, наблюдения, фото."""

from datetime import date, datetime
from decimal import Decimal

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
    UniqueConstraint,
    false,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base
from core.models.enums import PhotoKind, TaskStatus
from core.models.types import BigIntPK, CreatedAt, pg_enum, point_type, tz


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint("point_id", "date", name="uq_tasks_point_id_date"),
        Index("ix_tasks_user_id_date", "user_id", "date"),
        Index("ix_tasks_date_status", "date", "status"),
    )

    id: Mapped[BigIntPK]
    point_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("control_points.id"))
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    date: Mapped[date] = mapped_column(Date)
    status: Mapped[TaskStatus] = mapped_column(
        pg_enum(TaskStatus, "task_status"), server_default=TaskStatus.pending.value
    )
    done_at: Mapped[datetime | None] = mapped_column(tz())


class Observation(Base):
    __tablename__ = "observations"
    __table_args__ = (Index("ix_observations_point_id_taken_at", "point_id", "taken_at"),)

    id: Mapped[BigIntPK]
    task_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("tasks.id"), index=True)
    point_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("control_points.id"))
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    location: Mapped[str] = mapped_column(point_type())
    distance_m: Mapped[Decimal | None] = mapped_column(Numeric)
    taken_at: Mapped[datetime] = mapped_column(tz())
    plants_inspected: Mapped[int] = mapped_column(Integer, server_default=text("10"))
    plants_affected: Mapped[int] = mapped_column(Integer)
    wet_leaves: Mapped[bool] = mapped_column(Boolean)
    is_unplanned: Mapped[bool] = mapped_column(Boolean)
    comment: Mapped[str | None] = mapped_column(Text)


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[BigIntPK]
    observation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("observations.id"), index=True
    )
    kind: Mapped[PhotoKind] = mapped_column(pg_enum(PhotoKind, "photo_kind"))
    s3_key: Mapped[str | None] = mapped_column(Text)
    tg_file_id: Mapped[str] = mapped_column(Text)
    tg_file_unique_id: Mapped[str] = mapped_column(Text)
    archive_msg_id: Mapped[int | None] = mapped_column(BigInteger)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    blur_score: Mapped[float] = mapped_column(Float)
    brightness: Mapped[float] = mapped_column(Float)
    quality_ok: Mapped[bool] = mapped_column(Boolean)
    keep_forever: Mapped[bool] = mapped_column(Boolean, server_default=false())
    created_at: Mapped[CreatedAt]
