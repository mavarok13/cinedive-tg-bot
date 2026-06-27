from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cinedive.app.database.models import UserMoodSession


class MoodSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active(self, *, user_id: int, now: datetime) -> UserMoodSession | None:
        statement = (
            select(UserMoodSession)
            .where(
                UserMoodSession.user_id == user_id,
                UserMoodSession.expires_at > now,
            )
            .order_by(UserMoodSession.created_at.desc())
            .limit(1)
        )
        return await self._session.scalar(statement)

    async def create(
        self,
        *,
        user_id: int,
        content_type: str,
        mood_tags: dict[str, Any],
        expires_at: datetime,
        max_runtime_minutes: int | None = None,
        company_type: str | None = None,
    ) -> UserMoodSession:
        mood_session = UserMoodSession(
            user_id=user_id,
            content_type=content_type,
            mood_tags=mood_tags,
            max_runtime_minutes=max_runtime_minutes,
            company_type=company_type,
            expires_at=expires_at,
        )
        self._session.add(mood_session)
        await self._session.flush()
        return mood_session
