from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from cinedive.app.bot.keyboards import is_menu_button_text
from cinedive.app.bot.keyboards.genres import genre_display_name
from cinedive.app.database.repositories import UserGenreRepository, UserRepository
from cinedive.app.localization import t, user_locale
from cinedive.app.utils.formatting import html_escape

router = Router(name="profile")


@router.message(F.text.func(lambda text: is_menu_button_text(text, "profile")))
async def profile_entry(message: Message, session: AsyncSession) -> None:
    telegram_user = message.from_user
    if telegram_user is None:
        return
    locale = user_locale(telegram_user)

    user = await UserRepository(session).get_by_telegram_id(telegram_user.id)
    if user is None:
        await message.answer(t(locale, "profile.create_first"))
        return

    genre_ids = await UserGenreRepository(session).list_external_ids(user_id=user.id, media_type="movie")
    genre_names = sorted(
        name for genre_id in genre_ids if (name := genre_display_name(locale, genre_id))
    )
    genre_text = (
        ", ".join(html_escape(name) for name in genre_names)
        if genre_names
        else t(locale, "profile.genres_empty")
    )
    name = html_escape(user.display_name or user.first_name or t(locale, "profile.unknown_name"))
    await message.answer(
        f"{t(locale, 'profile.title')}\n"
        f"{t(locale, 'profile.name', name=name)}\n"
        f"{t(locale, 'profile.favorite_genres', genres=genre_text)}"
    )
