from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cinedive.app.database.base import Base

if TYPE_CHECKING:
    from cinedive.app.database.models.media import MediaGenre
    from cinedive.app.database.models.user import User


class Genre(Base):
    __tablename__ = "genres"
    __table_args__ = (
        UniqueConstraint(
            "source",
            "external_id",
            "media_type",
            name="uq_genres_source_external_media_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    external_id: Mapped[int] = mapped_column(Integer, nullable=False)
    media_type: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    user_links: Mapped[list[UserGenre]] = relationship(
        back_populates="genre",
        cascade="all, delete-orphan",
    )
    media_links: Mapped[list[MediaGenre]] = relationship(
        back_populates="genre",
        cascade="all, delete-orphan",
    )


class UserGenre(Base):
    __tablename__ = "user_genres"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    genre_id: Mapped[int] = mapped_column(
        ForeignKey("genres.id", ondelete="CASCADE"),
        primary_key=True,
    )
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="genres")
    genre: Mapped[Genre] = relationship(back_populates="user_links")
