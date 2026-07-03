from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from cinedive.app.bot.keyboards import rating_keyboard
from cinedive.app.bot.states import RatingStates
from cinedive.app.database.repositories import MediaRepository, UserMediaRepository, UserRepository
from cinedive.app.localization import t, user_locale
from cinedive.app.utils.formatting import html_escape

router = Router(name="rating")


@router.callback_query(F.data.startswith("rate:"))
async def rate_media(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await callback.answer()
    await _ask_rating(callback, state, session, mark_watched=False)


@router.callback_query(F.data.startswith("watched:"))
async def mark_watched(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await callback.answer()
    await _ask_rating(callback, state, session, mark_watched=True)


@router.callback_query(F.data.startswith("rating:set:"))
async def save_rating_callback(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    await callback.answer()

    parsed = _rating_callback_data(callback.data)
    if parsed is None:
        return
    media_id, rating = parsed
    await _save_rating(
        callback.from_user.id,
        media_id,
        rating,
        user_locale(callback.from_user),
        callback.message,
        state,
        session,
    )


@router.message(RatingStates.waiting_rating)
async def save_rating_message(message: Message, state: FSMContext, session: AsyncSession) -> None:
    locale = user_locale(message.from_user)
    try:
        rating = int((message.text or "").strip())
    except ValueError:
        await message.answer(t(locale, "rating.invalid"))
        return
    if rating < 1 or rating > 10:
        await message.answer(t(locale, "rating.invalid"))
        return

    data = await state.get_data()
    media_id = data.get("rating_media_id")
    if not isinstance(media_id, int):
        await state.clear()
        await message.answer(t(locale, "rating.expired"))
        return

    await _save_rating(message.from_user.id, media_id, rating, locale, message, state, session)


async def _ask_rating(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    *,
    mark_watched: bool,
) -> None:
    locale = user_locale(callback.from_user)
    media_id = _media_id_from_callback(callback.data)
    if media_id is None:
        await _answer_message(callback.message, t(locale, "rating.invalid_media"))
        return

    user = await UserRepository(session).get_by_telegram_id(callback.from_user.id)
    if user is None:
        await _answer_message(callback.message, t(locale, "errors.use_start"))
        return

    card = await MediaRepository(session).get_card(
        media_id=media_id,
        language_code=_translation_language(locale),
    )
    if card is None:
        await _answer_message(callback.message, t(locale, "rating.invalid_media"))
        return

    if mark_watched:
        await UserMediaRepository(session).set_status(user_id=user.id, media_id=media_id, status="watched")
        await session.commit()

    await state.update_data(rating_media_id=media_id)
    await state.set_state(RatingStates.waiting_rating)
    await _answer_message(
        callback.message,
        t(locale, "rating.ask", title=html_escape(card.title)),
        reply_markup=rating_keyboard(media_id),
    )


async def _save_rating(
    telegram_id: int,
    media_id: int,
    rating: int,
    locale: str,
    message: Message | None,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    user = await UserRepository(session).get_by_telegram_id(telegram_id)
    if user is None:
        await _answer_message(message, t(locale, "errors.use_start"))
        return

    if await MediaRepository(session).get_card(media_id=media_id, language_code=_translation_language(locale)) is None:
        await state.clear()
        await _answer_message(message, t(locale, "rating.invalid_media"))
        return

    await UserMediaRepository(session).set_rating(user_id=user.id, media_id=media_id, rating=rating)
    await session.commit()
    await state.clear()
    await _answer_message(message, t(locale, "rating.saved", rating=rating))


def _media_id_from_callback(callback_data: str | None) -> int | None:
    if callback_data is None:
        return None
    try:
        return int(callback_data.rsplit(":", maxsplit=1)[1])
    except (IndexError, ValueError):
        return None


def _rating_callback_data(callback_data: str | None) -> tuple[int, int] | None:
    if callback_data is None:
        return None
    try:
        _, _, media_id, rating = callback_data.split(":", maxsplit=3)
        rating_value = int(rating)
        if rating_value < 1 or rating_value > 10:
            return None
        return int(media_id), rating_value
    except ValueError:
        return None


def _translation_language(locale: str) -> str:
    return "ru-RU" if locale == "ru" else "en-US"


async def _answer_message(message: Message | None, text: str, **kwargs: object) -> None:
    if isinstance(message, Message):
        await message.answer(text, **kwargs)
