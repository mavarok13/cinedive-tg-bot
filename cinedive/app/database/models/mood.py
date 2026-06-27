from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cinedive.app.database.base import Base

if TYPE_CHECKING:
    from cinedive.app.database.models.user import User


class UserMoodSession(Base):
    __tablename__ = "user_mood_sessions"
    __table_args__ = (
        CheckConstraint(
            "content_type IN ('movie', 'tv', 'any')",
            name="ck_user_mood_sessions_content_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    content_type: Mapped[str] = mapped_column(String(16), nullable=False)
    mood_tags: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    max_runtime_minutes: Mapped[int | None] = mapped_column(Integer)
    company_type: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped[User] = relationship(back_populates="mood_sessions")
