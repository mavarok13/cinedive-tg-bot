from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from cinedive.app.database.models import RecommendationQueueItem, UserPreferencePenalty


@dataclass(frozen=True)
class RecommendationQueueDraft:
    media_id: int
    bucket: str
    score: float


class RecommendationQueueRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def clear_for_user(self, *, user_id: int) -> None:
        await self._session.execute(
            delete(RecommendationQueueItem).where(RecommendationQueueItem.user_id == user_id)
        )
        await self._session.flush()

    async def clear_for_session(self, *, mood_session_id: int) -> None:
        await self._session.execute(
            delete(RecommendationQueueItem).where(RecommendationQueueItem.mood_session_id == mood_session_id)
        )
        await self._session.flush()

    async def enqueue_batch(
        self,
        *,
        user_id: int,
        mood_session_id: int,
        expires_at: datetime,
        items: list[RecommendationQueueDraft],
    ) -> None:
        await self.clear_for_session(mood_session_id=mood_session_id)
        for position, item in enumerate(items):
            self._session.add(
                RecommendationQueueItem(
                    user_id=user_id,
                    mood_session_id=mood_session_id,
                    media_id=item.media_id,
                    position=position,
                    bucket=item.bucket,
                    score=item.score,
                    expires_at=expires_at,
                )
            )
        await self._session.flush()

    async def next_unshown(
        self,
        *,
        user_id: int,
        mood_session_id: int,
        now: datetime,
    ) -> RecommendationQueueItem | None:
        statement = (
            select(RecommendationQueueItem)
            .where(
                RecommendationQueueItem.user_id == user_id,
                RecommendationQueueItem.mood_session_id == mood_session_id,
                RecommendationQueueItem.expires_at > now,
                RecommendationQueueItem.shown_at.is_(None),
            )
            .order_by(RecommendationQueueItem.position)
            .limit(1)
        )
        return await self._session.scalar(statement)

    async def mark_shown(self, *, queue_item_id: int, shown_at: datetime) -> None:
        queue_item = await self._session.get(RecommendationQueueItem, queue_item_id)
        if queue_item is None:
            return
        queue_item.shown_at = shown_at
        await self._session.flush()


class UserPreferencePenaltyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def active_penalties(self, *, user_id: int, now: datetime) -> dict[tuple[str, str], float]:
        statement = select(UserPreferencePenalty).where(
            UserPreferencePenalty.user_id == user_id,
            (UserPreferencePenalty.expires_at.is_(None)) | (UserPreferencePenalty.expires_at > now),
        )
        penalties = await self._session.scalars(statement)
        return {
            (penalty.feature_type, penalty.feature_value): penalty.weight
            for penalty in penalties
        }

    async def add_penalty(
        self,
        *,
        user_id: int,
        feature_type: str,
        feature_value: str,
        weight_delta: float,
        expires_at: datetime,
        max_weight: float = 2.0,
    ) -> UserPreferencePenalty:
        statement = select(UserPreferencePenalty).where(
            UserPreferencePenalty.user_id == user_id,
            UserPreferencePenalty.feature_type == feature_type,
            UserPreferencePenalty.feature_value == feature_value,
        )
        penalty = await self._session.scalar(statement)
        if penalty is None:
            penalty = UserPreferencePenalty(
                user_id=user_id,
                feature_type=feature_type,
                feature_value=feature_value,
                weight=0.0,
            )
            self._session.add(penalty)
        elif penalty.expires_at is not None and penalty.expires_at <= datetime.now(UTC):
            penalty.weight = 0.0
        penalty.weight = min(penalty.weight + weight_delta, max_weight)
        penalty.expires_at = expires_at
        await self._session.flush()
        return penalty
