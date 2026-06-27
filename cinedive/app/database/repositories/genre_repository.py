from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from cinedive.app.database.models import Genre, UserGenre


class GenreRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(
        self,
        *,
        source: str,
        external_id: int,
        media_type: str,
        name: str,
    ) -> Genre:
        statement = select(Genre).where(
            Genre.source == source,
            Genre.external_id == external_id,
            Genre.media_type == media_type,
        )
        genre = await self._session.scalar(statement)
        if genre is None:
            genre = Genre(
                source=source,
                external_id=external_id,
                media_type=media_type,
                name=name,
            )
            self._session.add(genre)
            await self._session.flush()
        elif genre.name != name:
            genre.name = name
        return genre

    async def list_by_media_type(self, *, source: str, media_type: str) -> list[Genre]:
        statement = (
            select(Genre)
            .where(Genre.source == source, Genre.media_type == media_type)
            .order_by(Genre.name)
        )
        result = await self._session.scalars(statement)
        return list(result)


class UserGenreRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def has_any(self, user_id: int) -> bool:
        statement = select(UserGenre.user_id).where(UserGenre.user_id == user_id).limit(1)
        return await self._session.scalar(statement) is not None

    async def is_selected(self, *, user_id: int, genre_id: int) -> bool:
        statement = select(UserGenre).where(
            UserGenre.user_id == user_id,
            UserGenre.genre_id == genre_id,
        )
        return await self._session.scalar(statement) is not None

    async def add(self, *, user_id: int, genre_id: int, weight: float = 1.0) -> None:
        if await self.is_selected(user_id=user_id, genre_id=genre_id):
            return
        self._session.add(UserGenre(user_id=user_id, genre_id=genre_id, weight=weight))
        await self._session.flush()

    async def remove(self, *, user_id: int, genre_id: int) -> None:
        statement = delete(UserGenre).where(
            UserGenre.user_id == user_id,
            UserGenre.genre_id == genre_id,
        )
        await self._session.execute(statement)

    async def list_external_ids(
        self,
        *,
        user_id: int,
        source: str = "tmdb",
        media_type: str | None = None,
    ) -> set[int]:
        statement = select(Genre.external_id).join(UserGenre).where(
            UserGenre.user_id == user_id,
            Genre.source == source,
        )
        if media_type is not None:
            statement = statement.where(Genre.media_type == media_type)
        result = await self._session.scalars(statement)
        return set(result)

    async def list_names(self, *, user_id: int) -> list[str]:
        statement = select(Genre.name).join(UserGenre).where(UserGenre.user_id == user_id).order_by(
            Genre.name
        )
        result = await self._session.scalars(statement)
        return list(result)
