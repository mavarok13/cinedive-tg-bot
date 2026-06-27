from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cinedive.app.database.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        statement = select(User).where(User.telegram_id == telegram_id)
        return await self._session.scalar(statement)

    async def create_or_update(
        self,
        *,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        display_name: str | None,
        language_code: str | None,
    ) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = User(telegram_id=telegram_id)
            self._session.add(user)

        user.username = username
        user.first_name = first_name
        user.display_name = display_name
        user.language_code = language_code
        await self._session.flush()
        return user
