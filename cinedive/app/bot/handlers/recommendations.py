from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
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
    GenreRepository,
    MediaRepository,
    MoodSessionRepository,
    RecommendationQueueRepository,
    UserGenreRepository,
    UserMediaRepository,
    UserPreferencePenaltyRepository,
    UserRepository,
)
from cinedive.app.localization import t, user_locale
from cinedive.app.services.mood_service import MoodService
from cinedive.app.services.recommendation_service import RecommendationService
from cinedive.app.services.tmdb_service import TMDBService

router = Router(name="recommendations")

MAX_DISCOVER_RESULTS = 12
RECOMMENDATION_BATCH_SIZE = 30
PENALTY_TTL_DAYS = 45


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

    now = datetime.now(UTC)
    mood_repo = MoodSessionRepository(session)
    await RecommendationQueueRepository(session).clear_for_user(user_id=user.id)
    await mood_repo.expire_active(user_id=user.id, now=now)
    mood_session = await mood_repo.create(
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

    mood_session = await MoodSessionRepository(session).get_active(user_id=user.id, now=datetime.now(UTC))
    hidden_until = mood_session.expires_at if mood_session is not None else MoodService().expires_at()
    await UserMediaRepository(session).hide_temporarily(
        user_id=user.id,
        media_id=media_id,
        hidden_until=hidden_until,
    )
    await _apply_hide_penalties(session=session, user_id=user.id, media_id=media_id)
    await session.commit()

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
    now = datetime.now(UTC)
    media_repo = MediaRepository(session)
    queue_repo = RecommendationQueueRepository(session)
    queue_item = await queue_repo.next_unshown(
        user_id=user_id,
        mood_session_id=mood_session.id,
        now=now,
    )
    if queue_item is None:
        await _build_recommendation_queue(
            session=session,
            user_id=user_id,
            locale=locale,
            mood_session=mood_session,
            now=now,
        )
        queue_item = await queue_repo.next_unshown(
            user_id=user_id,
            mood_session_id=mood_session.id,
            now=now,
        )

    if queue_item is None:
        await message.answer(t(locale, "recommendations.no_candidates"))
        return

    card = await media_repo.get_card(
        media_id=queue_item.media_id,
        language_code=_translation_language(locale),
    )
    if card is None:
        await queue_repo.mark_shown(queue_item_id=queue_item.id, shown_at=now)
        await session.commit()
        await message.answer(t(locale, "recommendations.no_candidates"))
        return

    await queue_repo.mark_shown(queue_item_id=queue_item.id, shown_at=now)
    await UserMediaRepository(session).mark_shown(
        user_id=user_id,
        media_id=queue_item.media_id,
        shown_at=now,
    )
    await session.commit()
    await send_media_card(message, card, get_settings(), locale)


async def _build_recommendation_queue(
    *,
    session: AsyncSession,
    user_id: int,
    locale: str,
    mood_session: UserMoodSession,
    now: datetime,
) -> None:
    media_repo = MediaRepository(session)
    favorite_genre_ids = await UserGenreRepository(session).list_external_ids(user_id=user_id)
    mood_genre_ids = _mood_genre_ids(mood_session.mood_tags)
    await _seed_discover_candidates(
        session=session,
        mood_session=mood_session,
        locale=locale,
        genre_ids=favorite_genre_ids | mood_genre_ids,
    )

    candidates = await media_repo.list_recommendation_candidates(
        user_id=user_id,
        language_code=_translation_language(locale),
        content_type=mood_session.content_type,
        max_runtime_minutes=mood_session.max_runtime_minutes,
        now=now,
        limit=200,
    )
    user_media_repo = UserMediaRepository(session)
    collaborative_scores = await user_media_repo.collaborative_rating_scores(
        user_id=user_id,
        favorite_genre_ids=favorite_genre_ids,
    )
    wishlist_scores = await user_media_repo.collaborative_wishlist_scores(
        user_id=user_id,
        favorite_genre_ids=favorite_genre_ids,
    )
    penalties = await UserPreferencePenaltyRepository(session).active_penalties(user_id=user_id, now=now)
    queue_items = RecommendationService().build_queue(
        candidates,
        favorite_genre_ids=favorite_genre_ids,
        mood_genre_ids=mood_genre_ids,
        collaborative_scores=collaborative_scores,
        wishlist_scores=wishlist_scores,
        preference_penalties=penalties,
        batch_size=RECOMMENDATION_BATCH_SIZE,
    )
    if not queue_items:
        return
    await RecommendationQueueRepository(session).enqueue_batch(
        user_id=user_id,
        mood_session_id=mood_session.id,
        expires_at=mood_session.expires_at,
        items=queue_items,
    )
    await session.commit()


async def _apply_hide_penalties(*, session: AsyncSession, user_id: int, media_id: int) -> None:
    features = await MediaRepository(session).get_recommendation_features(media_id=media_id)
    if features is None:
        return

    repo = UserPreferencePenaltyRepository(session)
    expires_at = datetime.now(UTC) + timedelta(days=PENALTY_TTL_DAYS)
    await repo.add_penalty(
        user_id=user_id,
        feature_type="media_type",
        feature_value=features.media_type,
        weight_delta=0.15,
        expires_at=expires_at,
    )
    if features.original_language:
        await repo.add_penalty(
            user_id=user_id,
            feature_type="original_language",
            feature_value=features.original_language,
            weight_delta=0.25,
            expires_at=expires_at,
        )
    if features.origin_country:
        await repo.add_penalty(
            user_id=user_id,
            feature_type="origin_country",
            feature_value=features.origin_country,
            weight_delta=0.35,
            expires_at=expires_at,
        )
    for genre_id in features.genre_external_ids:
        await repo.add_penalty(
            user_id=user_id,
            feature_type="genre",
            feature_value=str(genre_id),
            weight_delta=0.2,
            expires_at=expires_at,
        )


async def _seed_discover_candidates(
    *,
    session: AsyncSession,
    mood_session: UserMoodSession,
    locale: str,
    genre_ids: set[int],
) -> None:
    settings = get_settings()
    tmdb: TMDBService | None = None
    try:
        tmdb = TMDBService(settings)
        for media_type in _discover_media_types(mood_session.content_type):
            results = []
            for sort_by, page in (
                ("vote_average.desc", 1),
                ("popularity.desc", 1),
                ("vote_count.desc", 1),
                ("vote_average.desc", 2),
            ):
                results.extend(
                    await tmdb.discover_media(
                        media_type=media_type,
                        language=_tmdb_language(locale),
                        genre_ids=_discover_genre_ids(media_type, genre_ids),
                        max_runtime_minutes=mood_session.max_runtime_minutes,
                        sort_by=sort_by,
                        page=page,
                    )
                )
            seen_tmdb_ids: set[int] = set()
            for result in results:
                tmdb_id = result.get("id")
                if not isinstance(tmdb_id, int) or tmdb_id in seen_tmdb_ids:
                    continue
                seen_tmdb_ids.add(tmdb_id)
                details = await _fetch_details(tmdb, tmdb_id, media_type, _tmdb_language(locale))
                await _persist_media_details(session, tmdb, details, media_type, locale)
                if len(seen_tmdb_ids) >= MAX_DISCOVER_RESULTS:
                    break
        await session.commit()
    except (httpx.HTTPError, RuntimeError, ValueError):
        await session.rollback()
    finally:
        if tmdb is not None:
            await tmdb.aclose()


def _discover_media_types(content_type: str) -> tuple[str, ...]:
    if content_type in {"movie", "tv"}:
        return (content_type,)
    return ("movie", "tv")


def _discover_genre_ids(media_type: str, genre_ids: set[int]) -> set[int]:
    if media_type == "movie":
        return genre_ids
    tv_genre_ids = {
        16,
        18,
        35,
        37,
        80,
        99,
        9648,
        10751,
        10759,
        10762,
        10763,
        10764,
        10765,
        10766,
        10767,
        10768,
    }
    return genre_ids & tv_genre_ids


async def _fetch_details(
    tmdb: TMDBService,
    tmdb_id: int,
    media_type: str,
    language: str,
) -> dict[str, Any]:
    if media_type == "movie":
        return await tmdb.get_movie_details(tmdb_id, language)
    return await tmdb.get_tv_details(tmdb_id, language)


async def _persist_media_details(
    session: AsyncSession,
    tmdb: TMDBService,
    details: dict[str, Any],
    media_type: str,
    locale: str,
) -> None:
    details_id = details.get("id")
    if not isinstance(details_id, int):
        raise ValueError("TMDB details response does not contain an integer id.")

    media_repo = MediaRepository(session)
    media = await media_repo.upsert_media(
        source="tmdb",
        external_id=details_id,
        media_type=media_type,
        original_title=_original_title(details, media_type),
        original_language=details.get("original_language"),
        origin_country=_origin_country(details, media_type),
        release_year=_release_year(details.get("release_date") or details.get("first_air_date")),
        poster_path=details.get("poster_path"),
        backdrop_path=details.get("backdrop_path"),
        runtime_minutes=_runtime_minutes(details, media_type),
        tmdb_rating=details.get("vote_average"),
        tmdb_vote_count=details.get("vote_count"),
        imdb_id=_imdb_id(details),
    )
    await media_repo.upsert_translation(
        media_id=media.id,
        language_code=_translation_language(locale),
        title=_localized_title(details, media_type),
        overview=details.get("overview") or None,
    )

    genre_repo = GenreRepository(session)
    genre_names = await _canonical_genre_names(tmdb, media_type)
    genre_ids: list[int] = []
    for genre_data in details.get("genres", []):
        if not isinstance(genre_data, dict) or not isinstance(genre_data.get("id"), int):
            continue
        external_id = int(genre_data["id"])
        genre = await genre_repo.get_or_create(
            source="tmdb",
            external_id=external_id,
            media_type=media_type,
            name=genre_names.get(external_id) or str(genre_data.get("name") or external_id),
            update_name=external_id in genre_names,
        )
        genre_ids.append(genre.id)
    await media_repo.replace_genres(media_id=media.id, genre_ids=genre_ids)


async def _canonical_genre_names(tmdb: TMDBService, media_type: str) -> dict[int, str]:
    genres = await tmdb.get_genres(media_type, "en-US")
    return {
        genre["id"]: str(genre.get("name") or genre["id"])
        for genre in genres
        if isinstance(genre.get("id"), int)
    }


def _localized_title(details: dict[str, Any], media_type: str) -> str:
    if media_type == "movie":
        return str(details.get("title") or details.get("original_title") or details.get("id"))
    return str(details.get("name") or details.get("original_name") or details.get("id"))


def _original_title(details: dict[str, Any], media_type: str) -> str | None:
    if media_type == "movie":
        return details.get("original_title") or details.get("title")
    return details.get("original_name") or details.get("name")


def _release_year(date_value: object) -> int | None:
    if not isinstance(date_value, str) or len(date_value) < 4:
        return None
    try:
        return int(date_value[:4])
    except ValueError:
        return None


def _runtime_minutes(details: dict[str, Any], media_type: str) -> int | None:
    if media_type == "movie":
        runtime = details.get("runtime")
        return runtime if isinstance(runtime, int) and runtime > 0 else None
    runtimes = details.get("episode_run_time")
    if isinstance(runtimes, list):
        for runtime in runtimes:
            if isinstance(runtime, int) and runtime > 0:
                return runtime
    return None


def _origin_country(details: dict[str, Any], media_type: str) -> str | None:
    if media_type == "tv":
        countries = details.get("origin_country")
        if isinstance(countries, list):
            for country in countries:
                if isinstance(country, str) and country:
                    return country[:8]

    production_countries = details.get("production_countries")
    if isinstance(production_countries, list):
        for country_data in production_countries:
            if not isinstance(country_data, dict):
                continue
            country = country_data.get("iso_3166_1")
            if isinstance(country, str) and country:
                return country[:8]
    return None


def _imdb_id(details: dict[str, Any]) -> str | None:
    imdb_id = details.get("imdb_id")
    if isinstance(imdb_id, str) and imdb_id:
        return imdb_id
    external_ids = details.get("external_ids")
    if isinstance(external_ids, dict) and isinstance(external_ids.get("imdb_id"), str):
        return external_ids["imdb_id"]
    return None


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


def _tmdb_language(locale: str) -> str:
    return "ru-RU" if locale == "ru" else get_settings().default_language
