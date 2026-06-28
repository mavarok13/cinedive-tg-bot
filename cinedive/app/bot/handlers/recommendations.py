from datetime import UTC, datetime
from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from cinedive.app.bot.keyboards import is_menu_button_text, mood_presets_keyboard
from cinedive.app.bot.media_cards import send_media_card
from cinedive.app.bot.states import MoodStates
from cinedive.app.config import get_settings
from cinedive.app.database.models import UserMoodSession
from cinedive.app.database.repositories import (
    MediaRepository,
    MoodSessionRepository,
    UserGenreRepository,
    UserMediaRepository,
    UserRepository,
)
from cinedive.app.localization import t, user_locale
from cinedive.app.services.mood_service import MoodService
from cinedive.app.services.recommendation_service import RecommendationService

router = Router(name="recommendations")


@router.message(F.text.func(lambda text: is_menu_button_text(text, "recommend")))
async def recommend_entry(message: Message, state: FSMContext, session: AsyncSession) -> None:
    locale = user_locale(message.from_user)
    user = await UserRepository(session).get_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer(t(locale, "errors.use_start"))
        return

    mood_session = await MoodSessionRepository(session).get_active(user_id=user.id, now=datetime.now(UTC))
    if mood_session is None:
        await _ask_mood(message, state, locale)
        return

    await _send_recommendation(message, session, user.id, locale, mood_session)


@router.callback_query(F.data.startswith("mood:preset:"))
async def save_mood_preset(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    await callback.answer()

    locale = user_locale(callback.from_user)
    if not isinstance(callback.message, Message):
        return
    preset_key = callback.data.rsplit(":", maxsplit=1)[1] if callback.data else ""
    mood_service = MoodService()
    preset = mood_service.preset(preset_key)
    if preset is None:
        await callback.message.answer(t(locale, "mood.unknown"))
        return

    user = await UserRepository(session).get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.message.answer(t(locale, "errors.use_start"))
        return

    mood_session = await MoodSessionRepository(session).create(
        user_id=user.id,
        content_type=preset.content_type,
        mood_tags=mood_service.mood_tags(preset),
        expires_at=mood_service.expires_at(),
        max_runtime_minutes=preset.max_runtime_minutes,
        company_type=preset.company_type,
    )
    await session.commit()
    await state.clear()
    await callback.message.answer(t(locale, "mood.saved", mood=t(locale, f"mood.presets.{preset.key}")))
    await _send_recommendation(callback.message, session, user.id, locale, mood_session)


@router.callback_query(F.data.startswith("recommend:next"))
async def recommend_next(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()

    locale = user_locale(callback.from_user)
    if not isinstance(callback.message, Message):
        return
    user = await UserRepository(session).get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.message.answer(t(locale, "errors.use_start"))
        return

    media_id = _optional_media_id(callback.data)
    if media_id is not None:
        await UserMediaRepository(session).hide_temporarily(
            user_id=user.id,
            media_id=media_id,
            hidden_until=MoodService().expires_at(),
        )
        await session.commit()

    mood_session = await MoodSessionRepository(session).get_active(user_id=user.id, now=datetime.now(UTC))
    if mood_session is None:
        await _ask_mood(callback.message, None, locale)
        return

    await _send_recommendation(callback.message, session, user.id, locale, mood_session)


@router.callback_query(F.data.startswith("hide:"))
async def hide_media(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()

    locale = user_locale(callback.from_user)
    if not isinstance(callback.message, Message):
        return
    media_id = _optional_media_id(callback.data)
    if media_id is None:
        return

    user = await UserRepository(session).get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.message.answer(t(locale, "errors.use_start"))
        return

    await UserMediaRepository(session).hide_temporarily(
        user_id=user.id,
        media_id=media_id,
        hidden_until=MoodService().expires_at(),
    )
    await session.commit()

    mood_session = await MoodSessionRepository(session).get_active(user_id=user.id, now=datetime.now(UTC))
    if mood_session is None:
        await callback.message.answer(t(locale, "recommendations.hidden"))
        return
    await callback.message.answer(t(locale, "recommendations.hidden"))
    await _send_recommendation(callback.message, session, user.id, locale, mood_session)


async def _ask_mood(message: Message, state: FSMContext | None, locale: str) -> None:
    if state is not None:
        await state.set_state(MoodStates.waiting_preferences)
    await message.answer(t(locale, "mood.ask"), reply_markup=mood_presets_keyboard(locale))


async def _send_recommendation(
    message: Message,
    session: AsyncSession,
    user_id: int,
    locale: str,
    mood_session: UserMoodSession,
) -> None:
    media_repo = MediaRepository(session)
    candidates = await media_repo.list_recommendation_candidates(
        user_id=user_id,
        language_code=_translation_language(locale),
        content_type=mood_session.content_type,
        max_runtime_minutes=mood_session.max_runtime_minutes,
        now=datetime.now(UTC),
    )
    favorite_genre_ids = await UserGenreRepository(session).list_external_ids(user_id=user_id)
    mood_genre_ids = _mood_genre_ids(mood_session.mood_tags)
    recommendations = RecommendationService().recommend(
        candidates,
        favorite_genre_ids=favorite_genre_ids,
        mood_genre_ids=mood_genre_ids,
        limit=1,
    )
    if not recommendations:
        await message.answer(t(locale, "recommendations.no_candidates"))
        return

    await send_media_card(message, recommendations[0].card, get_settings(), locale)


def _mood_genre_ids(mood_tags: dict[str, Any]) -> set[int]:
    values = mood_tags.get("genre_external_ids")
    if not isinstance(values, list):
        return set()
    genre_ids: set[int] = set()
    for value in values:
        if isinstance(value, int):
            genre_ids.add(value)
    return genre_ids


def _optional_media_id(callback_data: str | None) -> int | None:
    if callback_data is None:
        return None
    try:
        return int(callback_data.rsplit(":", maxsplit=1)[1])
    except (IndexError, ValueError):
        return None


def _translation_language(locale: str) -> str:
    return "ru-RU" if locale == "ru" else "en-US"
