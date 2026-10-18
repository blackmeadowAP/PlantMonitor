"""Общие типы колонок: время, география, перечисления."""

import enum
from datetime import datetime
from typing import Annotated

from geoalchemy2 import Geography
from sqlalchemy import BigInteger, DateTime, Enum, Identity, func
from sqlalchemy.orm import mapped_column

# Первичный ключ bigint identity
BigIntPK = Annotated[int, mapped_column(BigInteger, Identity(), primary_key=True)]

# Время создания записи (UTC, timestamptz)
CreatedAt = Annotated[
    datetime, mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
]


def point_type() -> Geography:
    """geography(Point, 4326) с GIST-индексом."""
    return Geography(geometry_type="POINT", srid=4326, spatial_index=True)


def polygon_type() -> Geography:
    """geography(Polygon, 4326) с GIST-индексом."""
    return Geography(geometry_type="POLYGON", srid=4326, spatial_index=True)


def pg_enum(enum_cls: type[enum.Enum], name: str) -> Enum:
    """Postgres ENUM, хранящий значения (а не имена) членов перечисления."""
    return Enum(enum_cls, name=name, values_callable=lambda e: [m.value for m in e])


def tz() -> DateTime:
    """timestamptz."""
    return DateTime(timezone=True)
