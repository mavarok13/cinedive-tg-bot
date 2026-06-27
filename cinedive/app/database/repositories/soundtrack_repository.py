from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cinedive.app.database.models import Soundtrack


class SoundtrackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_media_id(self, media_id: int) -> list[Soundtrack]:
        statement = select(Soundtrack).where(Soundtrack.media_id == media_id).order_by(Soundtrack.id)
        result = await self._session.scalars(statement)
        return list(result)

    async def create(
        self,
        *,
        media_id: int,
        title: str,
        source: str,
        external_url: str,
        artist: str | None = None,
        preview_url: str | None = None,
    ) -> Soundtrack:
        soundtrack = Soundtrack(
            media_id=media_id,
            title=title,
            artist=artist,
            source=source,
            external_url=external_url,
            preview_url=preview_url,
        )
        self._session.add(soundtrack)
        await self._session.flush()
        return soundtrack
