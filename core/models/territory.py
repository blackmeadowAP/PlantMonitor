"""Территория: области, районы, предприятия."""

from sqlalchemy import BigInteger, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base
from core.models.types import BigIntPK, CreatedAt, point_type


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[BigIntPK]
    name: Mapped[str] = mapped_column(Text)


class District(Base):
    __tablename__ = "districts"

    id: Mapped[BigIntPK]
    region_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("regions.id"), index=True)
    name: Mapped[str] = mapped_column(Text)


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[BigIntPK]
    name: Mapped[str] = mapped_column(Text)
    district_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("districts.id"), index=True)
    location: Mapped[str] = mapped_column(point_type())
    created_at: Mapped[CreatedAt]

    def __repr__(self) -> str:
        return f"Organization(id={self.id}, name={self.name!r})"
