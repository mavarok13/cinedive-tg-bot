from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cinedive.app.database.base import Base

if TYPE_CHECKING:
    from cinedive.app.database.models.media import MediaItem


class Soundtrack(Base):
    __tablename__ = "soundtracks"

    id: Mapped[int] = mapped_column(primary_key=True)
    media_id: Mapped[int] = mapped_column(
        ForeignKey("media_items.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    artist: Mapped[str | None] = mapped_column(String(512))
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    external_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    preview_url: Mapped[str | None] = mapped_column(String(2048))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    media: Mapped[MediaItem] = relationship(back_populates="soundtracks")
