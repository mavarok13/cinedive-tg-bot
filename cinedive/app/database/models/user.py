from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cinedive.app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from cinedive.app.database.models.genre import UserGenre
    from cinedive.app.database.models.mood import UserMoodSession
    from cinedive.app.database.models.user_media import UserMedia


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(255))
    language_code: Mapped[str | None] = mapped_column(String(16))

    genres: Mapped[list[UserGenre]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    media: Mapped[list[UserMedia]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    mood_sessions: Mapped[list[UserMoodSession]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
