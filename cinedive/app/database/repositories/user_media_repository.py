from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cinedive.app.database.models import Genre, UserGenre, UserMedia


class UserMediaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, *, user_id: int, media_id: int) -> UserMedia | None:
        statement = select(UserMedia).where(
            UserMedia.user_id == user_id,
            UserMedia.media_id == media_id,
        )
        return await self._session.scalar(statement)

    async def set_status(self, *, user_id: int, media_id: int, status: str) -> UserMedia:
        now = datetime.now(UTC)
        user_media = await self.get(user_id=user_id, media_id=media_id)
        if user_media is None:
            user_media = UserMedia(user_id=user_id, media_id=media_id, status=status)
            self._session.add(user_media)
        else:
            user_media.status = status
        if status == "wishlist":
            user_media.wishlist_at = now
        elif status == "watched":
            user_media.watched_at = now
        elif status == "ignored":
            user_media.ignored_at = now
        user_media.last_interaction_at = now
        await self._session.flush()
        return user_media

    async def hide_temporarily(
        self,
        *,
        user_id: int,
        media_id: int,
        hidden_until: datetime,
    ) -> UserMedia:
        user_media = await self.set_status(user_id=user_id, media_id=media_id, status="hidden")
        user_media.temporary_hidden_until = hidden_until
        await self._session.flush()
        return user_media

    async def mark_shown(self, *, user_id: int, media_id: int, shown_at: datetime) -> UserMedia:
        user_media = await self.get(user_id=user_id, media_id=media_id)
        if user_media is None:
            user_media = UserMedia(user_id=user_id, media_id=media_id, status="shown")
            self._session.add(user_media)
        user_media.last_shown_at = shown_at
        user_media.shown_count = (user_media.shown_count or 0) + 1
        user_media.last_interaction_at = shown_at
        await self._session.flush()
        return user_media

    async def remove(self, *, user_id: int, media_id: int) -> None:
        user_media = await self.get(user_id=user_id, media_id=media_id)
        if user_media is None:
            return
        user_media.wishlist_at = None
        if user_media.status == "wishlist":
            if user_media.rating is not None or user_media.watched_at is not None:
                user_media.status = "watched"
            elif user_media.last_shown_at is not None:
                user_media.status = "shown"
            else:
                await self._session.delete(user_media)
        await self._session.flush()

    async def set_rating(self, *, user_id: int, media_id: int, rating: int) -> UserMedia:
        user_media = await self.set_status(user_id=user_id, media_id=media_id, status="watched")
        user_media.rating = rating
        user_media.rated_at = datetime.now(UTC)
        await self._session.flush()
        return user_media

    async def list_wishlist(self, *, user_id: int) -> list[UserMedia]:
        statement = select(UserMedia).where(
            UserMedia.user_id == user_id,
            (UserMedia.status == "wishlist") | (UserMedia.wishlist_at.is_not(None)),
        )
        result = await self._session.scalars(statement)
        return list(result)

    async def collaborative_rating_scores(
        self,
        *,
        user_id: int,
        favorite_genre_ids: set[int],
        min_ratings: int = 3,
    ) -> dict[int, float]:
        if not favorite_genre_ids:
            return {}

        similar_users_statement = (
            select(UserGenre.user_id)
            .join(Genre)
            .where(
                UserGenre.user_id != user_id,
                Genre.external_id.in_(favorite_genre_ids),
            )
            .distinct()
        )
        similar_user_ids = set(await self._session.scalars(similar_users_statement))
        if not similar_user_ids:
            return {}

        ratings_statement = select(UserMedia.media_id, UserMedia.rating).where(
            UserMedia.user_id.in_(similar_user_ids),
            UserMedia.rating.is_not(None),
        )
        rows = list(await self._session.execute(ratings_statement))
        if len(rows) < min_ratings:
            return {}

        ratings_by_media: dict[int, list[int]] = {}
        for media_id, rating in rows:
            if isinstance(rating, int):
                ratings_by_media.setdefault(media_id, []).append(rating)
        return {
            media_id: min((sum(ratings) / len(ratings)) / 10, 1.0)
            for media_id, ratings in ratings_by_media.items()
        }

    async def collaborative_wishlist_scores(
        self,
        *,
        user_id: int,
        favorite_genre_ids: set[int],
        min_wishlist_items: int = 3,
    ) -> dict[int, float]:
        similar_user_ids = await self._similar_user_ids(
            user_id=user_id,
            favorite_genre_ids=favorite_genre_ids,
        )
        if not similar_user_ids:
            return {}

        wishlist_statement = select(UserMedia.media_id).where(
            UserMedia.user_id.in_(similar_user_ids),
            (UserMedia.status == "wishlist") | (UserMedia.wishlist_at.is_not(None)),
        )
        media_ids = list(await self._session.scalars(wishlist_statement))
        if len(media_ids) < min_wishlist_items:
            return {}

        counts: dict[int, int] = {}
        for media_id in media_ids:
            counts[media_id] = counts.get(media_id, 0) + 1
        max_count = max(counts.values())
        return {media_id: count / max_count for media_id, count in counts.items()}

    async def _similar_user_ids(self, *, user_id: int, favorite_genre_ids: set[int]) -> set[int]:
        if not favorite_genre_ids:
            return set()

        similar_users_statement = (
            select(UserGenre.user_id)
            .join(Genre)
            .where(
                UserGenre.user_id != user_id,
                Genre.external_id.in_(favorite_genre_ids),
            )
            .distinct()
        )
        return set(await self._session.scalars(similar_users_statement))
