from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from cinedive.app.database.models import UserMedia


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
        user_media = await self.get(user_id=user_id, media_id=media_id)
        if user_media is None:
            user_media = UserMedia(user_id=user_id, media_id=media_id, status=status)
            self._session.add(user_media)
        else:
            user_media.status = status
        await self._session.flush()
        return user_media

    async def remove(self, *, user_id: int, media_id: int) -> None:
        statement = delete(UserMedia).where(
            UserMedia.user_id == user_id,
            UserMedia.media_id == media_id,
        )
        await self._session.execute(statement)
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
            UserMedia.status == "wishlist",
        )
        result = await self._session.scalars(statement)
        return list(result)
