from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from cinedive.app.database.models import MediaGenre, MediaItem, MediaTranslation


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

    async def upsert_media(
        self,
        *,
        source: str,
        external_id: int,
        media_type: str,
        original_title: str | None,
        original_language: str | None,
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

    async def replace_genres(self, *, media_id: int, genre_ids: list[int]) -> None:
        await self._session.execute(delete(MediaGenre).where(MediaGenre.media_id == media_id))
        for genre_id in dict.fromkeys(genre_ids):
            self._session.add(MediaGenre(media_id=media_id, genre_id=genre_id))
        await self._session.flush()
