from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from cinedive.app.database.models import Genre, MediaGenre, MediaItem, MediaTranslation, UserMedia


@dataclass(frozen=True)
class MediaCardData:
    id: int
    media_type: str
    title: str
    overview: str | None
    release_year: int | None
    poster_path: str | None
    runtime_minutes: int | None
    tmdb_rating: float | None
    tmdb_vote_count: int | None


@dataclass(frozen=True)
class RecommendationCandidate:
    card: MediaCardData
    genre_external_ids: set[int]
    original_language: str | None
    origin_country: str | None
    shown_count: int = 0


@dataclass(frozen=True)
class RecommendationFeatureData:
    media_type: str
    original_language: str | None
    origin_country: str | None
    genre_external_ids: set[int]


class MediaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_external_id(
        self,
        *,
        source: str,
        external_id: int,
        media_type: str,
    ) -> MediaItem | None:
        statement = select(MediaItem).where(
            MediaItem.source == source,
            MediaItem.external_id == external_id,
            MediaItem.media_type == media_type,
        )
        return await self._session.scalar(statement)

    async def get_card(self, *, media_id: int, language_code: str) -> MediaCardData | None:
        media = await self._session.get(MediaItem, media_id)
        if media is None:
            return None

        translation = await self._get_translation(media_id=media.id, language_code=language_code)
        if translation is None and language_code != "en-US":
            translation = await self._get_translation(media_id=media.id, language_code="en-US")

        title = media.original_title or str(media.external_id)
        overview = None
        if translation is not None:
            title = translation.title
            overview = translation.overview
        if language_code != "en-US" and not overview:
            fallback_translation = await self._get_translation(media_id=media.id, language_code="en-US")
            if fallback_translation is not None:
                overview = fallback_translation.overview

        return MediaCardData(
            id=media.id,
            media_type=media.media_type,
            title=title,
            overview=overview,
            release_year=media.release_year,
            poster_path=media.poster_path,
            runtime_minutes=media.runtime_minutes,
            tmdb_rating=media.tmdb_rating,
            tmdb_vote_count=media.tmdb_vote_count,
        )

    async def get_recommendation_features(self, *, media_id: int) -> RecommendationFeatureData | None:
        media = await self._session.get(MediaItem, media_id)
        if media is None:
            return None
        return RecommendationFeatureData(
            media_type=media.media_type,
            original_language=media.original_language,
            origin_country=media.origin_country,
            genre_external_ids=await self._genre_external_ids(media_id=media.id),
        )

    async def list_recommendation_candidates(
        self,
        *,
        user_id: int,
        language_code: str,
        content_type: str,
        now: datetime,
        max_runtime_minutes: int | None = None,
        limit: int = 100,
        shown_cooldown_days: int = 30,
        exclude_media_ids: set[int] | None = None,
    ) -> list[RecommendationCandidate]:
        exclude_media_ids = exclude_media_ids or set()
        statement = select(MediaItem)
        if content_type in {"movie", "tv"}:
            statement = statement.where(MediaItem.media_type == content_type)
        if exclude_media_ids:
            statement = statement.where(MediaItem.id.not_in(exclude_media_ids))
        if max_runtime_minutes is not None:
            statement = statement.where(
                (MediaItem.runtime_minutes.is_(None))
                | (MediaItem.runtime_minutes <= max_runtime_minutes)
            )
        statement = statement.where(MediaItem.poster_path.is_not(None))
        statement = statement.order_by(
            MediaItem.tmdb_rating.desc().nullslast(),
            MediaItem.tmdb_vote_count.desc().nullslast(),
        ).limit(limit)

        media_items = list(await self._session.scalars(statement))
        candidates: list[RecommendationCandidate] = []
        for media in media_items:
            user_media = await self._get_user_media(user_id=user_id, media_id=media.id)
            if _is_excluded_user_media(user_media, now, shown_cooldown_days):
                continue
            card = await self.get_card(media_id=media.id, language_code=language_code)
            if card is None or not card.poster_path or not card.overview:
                continue
            candidates.append(
                RecommendationCandidate(
                    card=card,
                    genre_external_ids=await self._genre_external_ids(media_id=media.id),
                    original_language=media.original_language,
                    origin_country=media.origin_country,
                    shown_count=user_media.shown_count if user_media is not None else 0,
                )
            )
        return candidates

    async def upsert_media(
        self,
        *,
        source: str,
        external_id: int,
        media_type: str,
        original_title: str | None,
        original_language: str | None,
        origin_country: str | None,
        release_year: int | None,
        poster_path: str | None,
        backdrop_path: str | None,
        runtime_minutes: int | None,
        tmdb_rating: float | None,
        tmdb_vote_count: int | None,
        imdb_id: str | None = None,
    ) -> MediaItem:
        media = await self.get_by_external_id(
            source=source,
            external_id=external_id,
            media_type=media_type,
        )
        if media is None:
            media = MediaItem(source=source, external_id=external_id, media_type=media_type)
            self._session.add(media)

        media.imdb_id = imdb_id
        media.original_title = original_title
        media.original_language = original_language
        media.origin_country = origin_country
        media.release_year = release_year
        media.poster_path = poster_path
        media.backdrop_path = backdrop_path
        media.runtime_minutes = runtime_minutes
        media.tmdb_rating = tmdb_rating
        media.tmdb_vote_count = tmdb_vote_count
        await self._session.flush()
        return media

    async def upsert_translation(
        self,
        *,
        media_id: int,
        language_code: str,
        title: str,
        overview: str | None,
    ) -> MediaTranslation:
        statement = select(MediaTranslation).where(
            MediaTranslation.media_id == media_id,
            MediaTranslation.language_code == language_code,
        )
        translation = await self._session.scalar(statement)
        if translation is None:
            translation = MediaTranslation(media_id=media_id, language_code=language_code)
            self._session.add(translation)

        translation.title = title
        translation.overview = overview
        await self._session.flush()
        return translation

    async def _get_translation(
        self,
        *,
        media_id: int,
        language_code: str,
    ) -> MediaTranslation | None:
        statement = select(MediaTranslation).where(
            MediaTranslation.media_id == media_id,
            MediaTranslation.language_code == language_code,
        )
        return await self._session.scalar(statement)

    async def _genre_external_ids(self, *, media_id: int) -> set[int]:
        statement = select(Genre.external_id).join(MediaGenre).where(MediaGenre.media_id == media_id)
        result = await self._session.scalars(statement)
        return set(result)

    async def _get_user_media(self, *, user_id: int, media_id: int) -> UserMedia | None:
        statement = select(UserMedia).where(
            UserMedia.user_id == user_id,
            UserMedia.media_id == media_id,
        )
        return await self._session.scalar(statement)

    async def existing_external_ids(
        self,
        *,
        source: str,
        media_type: str,
        external_ids: set[int],
    ) -> dict[int, int]:
        if not external_ids:
            return {}
        statement = select(MediaItem.external_id, MediaItem.id).where(
            MediaItem.source == source,
            MediaItem.media_type == media_type,
            MediaItem.external_id.in_(external_ids),
        )
        return {external_id: media_id for external_id, media_id in await self._session.execute(statement)}

    async def replace_genres(self, *, media_id: int, genre_ids: list[int]) -> None:
        await self._session.execute(delete(MediaGenre).where(MediaGenre.media_id == media_id))
        for genre_id in dict.fromkeys(genre_ids):
            self._session.add(MediaGenre(media_id=media_id, genre_id=genre_id))
        await self._session.flush()


def _is_excluded_user_media(
    user_media: UserMedia | None,
    now: datetime,
    shown_cooldown_days: int,
) -> bool:
    if user_media is None:
        return False
    if user_media.status in {"watched", "ignored"} or user_media.rating is not None:
        return True
    if user_media.status == "hidden":
        return user_media.temporary_hidden_until is None or user_media.temporary_hidden_until > now
    if user_media.last_shown_at is not None:
        return user_media.last_shown_at > now - timedelta(days=shown_cooldown_days)
    return False
