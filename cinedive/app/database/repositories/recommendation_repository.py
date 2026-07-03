from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from cinedive.app.database.models import (
    RecommendationDiscoveryState,
    RecommendationQueueItem,
    UserMoodSession,
    UserPreferencePenalty,
)


@dataclass(frozen=True)
class RecommendationQueueDraft:
    media_id: int
    bucket: str
    score: float


@dataclass(frozen=True)
class DiscoveryStrategyDraft:
    media_type: str
    sort_by: str
    genre_key: str
    filter_key: str


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
        if not items:
            return

        existing_media_ids = await self.media_ids_for_session(mood_session_id=mood_session_id)
        start_position = await self._next_position(mood_session_id=mood_session_id)
        position = start_position
        for item in items:
            if item.media_id in existing_media_ids:
                continue
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
            existing_media_ids.add(item.media_id)
            position += 1
        await self._session.flush()

    async def media_ids_for_session(self, *, mood_session_id: int) -> set[int]:
        statement = select(RecommendationQueueItem.media_id).where(
            RecommendationQueueItem.mood_session_id == mood_session_id
        )
        return set(await self._session.scalars(statement))

    async def has_unshown(self, *, user_id: int, mood_session_id: int, now: datetime) -> bool:
        return await self.next_unshown(user_id=user_id, mood_session_id=mood_session_id, now=now) is not None

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

    async def claim_next_unshown(
        self,
        *,
        user_id: int,
        mood_session_id: int,
        now: datetime,
        shown_at: datetime,
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
            .with_for_update(skip_locked=True)
        )
        queue_item = await self._session.scalar(statement)
        if queue_item is None:
            return None
        queue_item.shown_at = shown_at
        await self._session.flush()
        return queue_item

    async def mark_shown(self, *, queue_item_id: int, shown_at: datetime) -> None:
        queue_item = await self._session.get(RecommendationQueueItem, queue_item_id)
        if queue_item is None:
            return
        queue_item.shown_at = shown_at
        await self._session.flush()

    async def lock_mood_session(self, *, mood_session_id: int) -> UserMoodSession | None:
        statement = (
            select(UserMoodSession)
            .where(UserMoodSession.id == mood_session_id)
            .with_for_update()
        )
        return await self._session.scalar(statement)

    async def _next_position(self, *, mood_session_id: int) -> int:
        statement = select(func.max(RecommendationQueueItem.position)).where(
            RecommendationQueueItem.mood_session_id == mood_session_id
        )
        max_position = await self._session.scalar(statement)
        if max_position is None:
            return 0
        return int(max_position) + 1


class RecommendationDiscoveryStateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ensure_states(
        self,
        *,
        user_id: int,
        mood_session_id: int,
        strategies: list[DiscoveryStrategyDraft],
    ) -> list[RecommendationDiscoveryState]:
        if not strategies:
            return []

        for strategy in strategies:
            statement = (
                pg_insert(RecommendationDiscoveryState)
                .values(
                    user_id=user_id,
                    mood_session_id=mood_session_id,
                    media_type=strategy.media_type,
                    sort_by=strategy.sort_by,
                    genre_key=strategy.genre_key,
                    filter_key=strategy.filter_key,
                    next_page=1,
                    attempt_count=0,
                    empty_result_count=0,
                    exhausted=False,
                )
                .on_conflict_do_nothing(
                    constraint="uq_recommendation_discovery_strategy",
                )
            )
            await self._session.execute(statement)
        await self._session.flush()

        statement = select(RecommendationDiscoveryState).where(
            RecommendationDiscoveryState.mood_session_id == mood_session_id,
            RecommendationDiscoveryState.exhausted.is_(False),
        )
        states = list(await self._session.scalars(statement))
        return sorted(states, key=_discovery_state_sort_key)

    async def record_attempt(
        self,
        *,
        state: RecommendationDiscoveryState,
        next_page: int,
        empty: bool,
        exhausted: bool,
        used_at: datetime,
    ) -> None:
        state.next_page = next_page
        state.attempt_count += 1
        state.empty_result_count = state.empty_result_count + 1 if empty else 0
        state.exhausted = exhausted
        state.last_used_at = used_at
        await self._session.flush()


def _discovery_state_sort_key(state: RecommendationDiscoveryState) -> tuple[datetime, int, int]:
    return (
        state.last_used_at or datetime.min.replace(tzinfo=UTC),
        state.attempt_count,
        state.id,
    )


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
