from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from cinedive.app.bot.keyboards import favorite_genres_keyboard, main_menu_keyboard
from cinedive.app.database.repositories import UserGenreRepository, UserRepository
from cinedive.app.localization import t, user_locale
from cinedive.app.utils.formatting import html_escape

router = Router(name="start")


@router.message(CommandStart())
async def start_command(message: Message, session: AsyncSession) -> None:
    telegram_user = message.from_user
    if telegram_user is None:
        return

    user = await UserRepository(session).create_or_update(
        telegram_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        display_name=telegram_user.full_name,
        language_code=telegram_user.language_code,
    )
    has_genres = await UserGenreRepository(session).has_any(user.id)
    await session.commit()

    locale = user_locale(telegram_user)
    name = html_escape(user.display_name or user.first_name or t(locale, "start.fallback_name"))
    if has_genres:
        await message.answer(
            t(locale, "start.welcome_back", name=name),
            reply_markup=main_menu_keyboard(locale),
        )
        return

    await message.answer(
        t(locale, "start.onboarding_intro", name=name),
        reply_markup=favorite_genres_keyboard(set(), locale),
    )
