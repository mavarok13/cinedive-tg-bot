from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cinedive.app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from cinedive.app.database.models.media import MediaItem
    from cinedive.app.database.models.mood import UserMoodSession
    from cinedive.app.database.models.user import User


class RecommendationQueueItem(Base):
    __tablename__ = "recommendation_queue_items"
    __table_args__ = (
        CheckConstraint(
            "bucket IN ('high', 'medium', 'exploration')",
            name="ck_recommendation_queue_bucket",
        ),
        UniqueConstraint(
            "mood_session_id",
            "position",
            name="uq_recommendation_queue_session_position",
        ),
        UniqueConstraint(
            "mood_session_id",
            "media_id",
            name="uq_recommendation_queue_session_media",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    mood_session_id: Mapped[int] = mapped_column(
        ForeignKey("user_mood_sessions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    media_id: Mapped[int] = mapped_column(ForeignKey("media_items.id", ondelete="CASCADE"), index=True, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    bucket: Mapped[str] = mapped_column(String(16), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    shown_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped[User] = relationship()
    mood_session: Mapped[UserMoodSession] = relationship()
    media: Mapped[MediaItem] = relationship()


class RecommendationDiscoveryState(TimestampMixin, Base):
    __tablename__ = "recommendation_discovery_states"
    __table_args__ = (
        CheckConstraint(
            "media_type IN ('movie', 'tv')",
            name="ck_recommendation_discovery_media_type",
        ),
        UniqueConstraint(
            "mood_session_id",
            "media_type",
            "sort_by",
            "genre_key",
            "filter_key",
            name="uq_recommendation_discovery_strategy",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    mood_session_id: Mapped[int] = mapped_column(
        ForeignKey("user_mood_sessions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    media_type: Mapped[str] = mapped_column(String(16), nullable=False)
    sort_by: Mapped[str] = mapped_column(String(64), nullable=False)
    genre_key: Mapped[str] = mapped_column(String(256), nullable=False)
    filter_key: Mapped[str] = mapped_column(String(256), nullable=False)
    next_page: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    empty_result_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    exhausted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    user: Mapped[User] = relationship()
    mood_session: Mapped[UserMoodSession] = relationship()


class UserPreferencePenalty(TimestampMixin, Base):
    __tablename__ = "user_preference_penalties"
    __table_args__ = (
        CheckConstraint(
            "feature_type IN ('genre', 'origin_country', 'original_language', 'media_type')",
            name="ck_user_preference_penalties_feature_type",
        ),
        UniqueConstraint(
            "user_id",
            "feature_type",
            "feature_value",
            name="uq_user_preference_penalty_feature",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    feature_type: Mapped[str] = mapped_column(String(32), nullable=False)
    feature_value: Mapped[str] = mapped_column(String(128), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    user: Mapped[User] = relationship()
