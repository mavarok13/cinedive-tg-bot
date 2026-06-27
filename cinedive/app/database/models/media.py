from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cinedive.app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from cinedive.app.database.models.genre import Genre
    from cinedive.app.database.models.soundtrack import Soundtrack
    from cinedive.app.database.models.user_media import UserMedia


class MediaItem(TimestampMixin, Base):
    __tablename__ = "media_items"
    __table_args__ = (
        UniqueConstraint(
            "source",
            "external_id",
            "media_type",
            name="uq_media_items_source_external_media_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    external_id: Mapped[int] = mapped_column(Integer, nullable=False)
    imdb_id: Mapped[str | None] = mapped_column(String(32))
    media_type: Mapped[str] = mapped_column(String(16), nullable=False)
    original_title: Mapped[str | None] = mapped_column(String(512))
    original_language: Mapped[str | None] = mapped_column(String(16))
    release_year: Mapped[int | None] = mapped_column(Integer)
    poster_path: Mapped[str | None] = mapped_column(String(512))
    backdrop_path: Mapped[str | None] = mapped_column(String(512))
    runtime_minutes: Mapped[int | None] = mapped_column(Integer)
    tmdb_rating: Mapped[float | None] = mapped_column(Float)
    tmdb_vote_count: Mapped[int | None] = mapped_column(Integer)

    translations: Mapped[list[MediaTranslation]] = relationship(
        back_populates="media",
        cascade="all, delete-orphan",
    )
    genres: Mapped[list[MediaGenre]] = relationship(
        back_populates="media",
        cascade="all, delete-orphan",
    )
    user_links: Mapped[list[UserMedia]] = relationship(
        back_populates="media",
        cascade="all, delete-orphan",
    )
    soundtracks: Mapped[list[Soundtrack]] = relationship(
        back_populates="media",
        cascade="all, delete-orphan",
    )


class MediaTranslation(Base):
    __tablename__ = "media_translations"
    __table_args__ = (
        UniqueConstraint("media_id", "language_code", name="uq_media_translations_media_language"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    media_id: Mapped[int] = mapped_column(
        ForeignKey("media_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    language_code: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    overview: Mapped[str | None] = mapped_column(Text)

    media: Mapped[MediaItem] = relationship(back_populates="translations")


class MediaGenre(Base):
    __tablename__ = "media_genres"

    media_id: Mapped[int] = mapped_column(
        ForeignKey("media_items.id", ondelete="CASCADE"),
        primary_key=True,
    )
    genre_id: Mapped[int] = mapped_column(
        ForeignKey("genres.id", ondelete="CASCADE"),
        primary_key=True,
    )

    media: Mapped[MediaItem] = relationship(back_populates="genres")
    genre: Mapped[Genre] = relationship(back_populates="media_links")
