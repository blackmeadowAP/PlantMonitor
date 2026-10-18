"""Сообщения между пользователями."""

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base
from core.models.types import BigIntPK, tz


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[BigIntPK]
    from_user: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    to_user: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    # Рассылка: 'region:5' | 'district:12' | 'org:3'
    scope: Mapped[str | None] = mapped_column(Text)
    ref_type: Mapped[str | None] = mapped_column(Text)
    ref_id: Mapped[int | None] = mapped_column(BigInteger)
    text: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(tz(), server_default=func.now())
