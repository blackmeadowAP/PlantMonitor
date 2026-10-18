"""Справочники: культуры и болезни."""

from typing import Any

from sqlalchemy import BigInteger, Boolean, ForeignKey, Text, true
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base
from core.models.types import BigIntPK


class Crop(Base):
    __tablename__ = "crops"

    id: Mapped[BigIntPK]
    name: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true())


class Disease(Base):
    __tablename__ = "diseases"

    id: Mapped[BigIntPK]
    crop_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("crops.id"), index=True)
    name: Mapped[str] = mapped_column(Text)
    latin_name: Mapped[str | None] = mapped_column(Text)
    severity_scale: Mapped[dict[str, Any]] = mapped_column(JSONB)
    reference_photo_keys: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true())
