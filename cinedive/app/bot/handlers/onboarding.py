from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from cinedive.app.bot.keyboards.genres import canonical_genre_name, favorite_genres_keyboard
from cinedive.app.bot.keyboards.menu import main_menu_keyboard
from cinedive.app.database.repositories import GenreRepository, UserGenreRepository, UserRepository
from cinedive.app.localization import t, user_locale

router = Router(name="onboarding")


def _genre_name(external_id: int) -> str | None:
    return canonical_genre_name(external_id)


@router.callback_query(F.data.startswith("genre:"))
async def toggle_favorite_genre(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()

    locale = user_locale(callback.from_user)
    telegram_user = callback.from_user
    user = await UserRepository(session).get_by_telegram_id(telegram_user.id)
    if user is None:
        if isinstance(callback.message, Message):
            await callback.message.answer(t(locale, "errors.use_start"))
        return

    try:
        external_id = int(callback.data.split(":", maxsplit=1)[1]) if callback.data else 0
    except ValueError:
        if isinstance(callback.message, Message):
            await callback.message.answer(t(locale, "errors.unknown_genre"))
        return
    name = _genre_name(external_id)
    if name is None:
        if isinstance(callback.message, Message):
            await callback.message.answer(t(locale, "errors.unknown_genre"))
        return

    genre = await GenreRepository(session).get_or_create(
        source="tmdb",
        external_id=external_id,
        media_type="movie",
        name=name,
    )
    user_genres = UserGenreRepository(session)
    if await user_genres.is_selected(user_id=user.id, genre_id=genre.id):
        await user_genres.remove(user_id=user.id, genre_id=genre.id)
    else:
        await user_genres.add(user_id=user.id, genre_id=genre.id)

    selected = await user_genres.list_external_ids(user_id=user.id, media_type="movie")
    await session.commit()

    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            t(locale, "onboarding.pick_genres"),
            reply_markup=favorite_genres_keyboard(selected, locale),
        )


@router.callback_query(F.data == "genre_done")
async def finish_genre_onboarding(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()

    locale = user_locale(callback.from_user)
    user = await UserRepository(session).get_by_telegram_id(callback.from_user.id)
    if user is None:
        if isinstance(callback.message, Message):
            await callback.message.answer(t(locale, "errors.use_start"))
        return

    selected = await UserGenreRepository(session).list_external_ids(user_id=user.id, media_type="movie")
    if not selected:
        if isinstance(callback.message, Message):
            await callback.message.answer(t(locale, "onboarding.choose_at_least_one"))
        return

    if isinstance(callback.message, Message):
        await callback.message.edit_text(t(locale, "onboarding.saved"))
        await callback.message.answer(t(locale, "menu.title"), reply_markup=main_menu_keyboard(locale))
