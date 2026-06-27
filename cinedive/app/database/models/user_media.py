from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cinedive.app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from cinedive.app.database.models.media import MediaItem
    from cinedive.app.database.models.user import User


class UserMedia(TimestampMixin, Base):
    __tablename__ = "user_media"
    __table_args__ = (
        CheckConstraint(
            "status IN ('wishlist', 'watched', 'hidden', 'ignored')",
            name="ck_user_media_status",
        ),
        CheckConstraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 10)",
            name="ck_user_media_rating_range",
        ),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    media_id: Mapped[int] = mapped_column(
        ForeignKey("media_items.id", ondelete="CASCADE"),
        primary_key=True,
    )
    status: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    rating: Mapped[int | None] = mapped_column(Integer)
    rated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    temporary_hidden_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="media")
    media: Mapped[MediaItem] = relationship(back_populates="user_links")
