from typing import Any

import httpx
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from cinedive.app.bot.keyboards import is_menu_button_text, search_results_keyboard
from cinedive.app.bot.media_cards import send_media_card
from cinedive.app.bot.states import SearchStates
from cinedive.app.config import Settings, get_settings
from cinedive.app.database.models import MediaItem
from cinedive.app.database.repositories import GenreRepository, MediaRepository
from cinedive.app.localization import t, user_locale
from cinedive.app.services.tmdb_service import TMDBService
from cinedive.app.utils.formatting import html_escape

router = Router(name="search")

MAX_SEARCH_RESULTS = 8


@router.message(F.text.func(lambda text: is_menu_button_text(text, "search")))
async def ask_search_query(message: Message, state: FSMContext) -> None:
    await state.set_state(SearchStates.waiting_query)
    locale = user_locale(message.from_user)
    await message.answer(t(locale, "search.ask_query"))


@router.message(SearchStates.waiting_query)
async def receive_search_query(message: Message, state: FSMContext) -> None:
    locale = user_locale(message.from_user)
    query = (message.text or "").strip()
    if not query:
        await message.answer(t(locale, "search.empty_query"))
        return

    settings = get_settings()
    tmdb: TMDBService | None = None
    try:
        tmdb = TMDBService(settings)
        results = await tmdb.search_media(query=query, language=_tmdb_language(locale, settings))
    except (httpx.HTTPError, RuntimeError):
        await message.answer(t(locale, "search.failed"))
        return
    finally:
        if tmdb is not None:
            await tmdb.aclose()

    choices = [_search_choice(result) for result in results[:MAX_SEARCH_RESULTS]]
    choices = [choice for choice in choices if choice is not None]
    if not choices:
        await state.clear()
        await message.answer(t(locale, "search.no_results"))
        return

    await state.update_data(search_results=choices)
    await state.set_state(SearchStates.waiting_selection)
    await message.answer(
        t(locale, "search.results_intro", query=html_escape(query)),
        reply_markup=search_results_keyboard(choices, locale),
    )


@router.message(SearchStates.waiting_selection)
async def prompt_search_selection(message: Message) -> None:
    locale = user_locale(message.from_user)
    await message.answer(t(locale, "search.choose_result"))


@router.callback_query(SearchStates.waiting_selection, F.data.startswith("search:select:"))
async def select_search_result(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    await callback.answer()

    locale = user_locale(callback.from_user)
    result = await _selected_result(callback, state)
    if result is None:
        await state.clear()
        if isinstance(callback.message, Message):
            await callback.message.answer(t(locale, "search.invalid_selection"))
        return

    settings = get_settings()
    tmdb: TMDBService | None = None
    try:
        tmdb = TMDBService(settings)
        details = await _fetch_details(tmdb, result, _tmdb_language(locale, settings))
        media = await _persist_media_details(session, tmdb, details, result["media_type"], locale)
        await session.commit()
        card = await MediaRepository(session).get_card(
            media_id=media.id,
            language_code=_translation_language(locale),
        )
    except (httpx.HTTPError, RuntimeError, ValueError):
        await session.rollback()
        if isinstance(callback.message, Message):
            await callback.message.answer(t(locale, "search.failed"))
        return
    finally:
        if tmdb is not None:
            await tmdb.aclose()

    await state.clear()
    if isinstance(callback.message, Message) and card is not None:
        await send_media_card(callback.message, card, settings, locale)


def _tmdb_language(locale: str, settings: Settings) -> str:
    if locale == "ru":
        return "ru-RU"
    return settings.default_language


def _search_choice(result: dict[str, Any]) -> dict[str, object] | None:
    media_type = result.get("media_type")
    external_id = result.get("id")
    if media_type not in {"movie", "tv"} or not isinstance(external_id, int):
        return None
    title = result.get("title") or result.get("name") or result.get("original_title") or result.get("original_name")
    if not title:
        return None
    date = result.get("release_date") or result.get("first_air_date")
    return {
        "id": external_id,
        "media_type": media_type,
        "title": str(title),
        "year": _release_year(date),
    }


async def _selected_result(callback: CallbackQuery, state: FSMContext) -> dict[str, Any] | None:
    if callback.data is None:
        return None
    try:
        index = int(callback.data.rsplit(":", maxsplit=1)[1])
    except (IndexError, ValueError):
        return None
    data = await state.get_data()
    results = data.get("search_results")
    if not isinstance(results, list) or index < 0 or index >= len(results):
        return None
    selected = results[index]
    return selected if isinstance(selected, dict) else None


async def _fetch_details(
    tmdb: TMDBService,
    result: dict[str, Any],
    language: str,
) -> dict[str, Any]:
    tmdb_id = int(result["id"])
    if result["media_type"] == "movie":
        return await tmdb.get_movie_details(tmdb_id, language)
    return await tmdb.get_tv_details(tmdb_id, language)


async def _persist_media_details(
    session: AsyncSession,
    tmdb: TMDBService,
    details: dict[str, Any],
    media_type: object,
    locale: str,
) -> MediaItem:
    if media_type not in {"movie", "tv"}:
        raise ValueError("Unsupported media type.")

    details_id = details.get("id")
    if not isinstance(details_id, int):
        raise ValueError("TMDB details response does not contain an integer id.")

    media_repo = MediaRepository(session)
    media = await media_repo.upsert_media(
        source="tmdb",
        external_id=details_id,
        media_type=str(media_type),
        original_title=_original_title(details, str(media_type)),
        original_language=details.get("original_language"),
        origin_country=_origin_country(details, str(media_type)),
        release_year=_release_year(details.get("release_date") or details.get("first_air_date")),
        poster_path=details.get("poster_path"),
        backdrop_path=details.get("backdrop_path"),
        runtime_minutes=_runtime_minutes(details, str(media_type)),
        tmdb_rating=details.get("vote_average"),
        tmdb_vote_count=details.get("vote_count"),
        imdb_id=_imdb_id(details),
    )
    await media_repo.upsert_translation(
        media_id=media.id,
        language_code=_translation_language(locale),
        title=_localized_title(details, str(media_type)),
        overview=details.get("overview") or None,
    )

    genre_repo = GenreRepository(session)
    genre_names = await _canonical_genre_names(tmdb, str(media_type))
    genre_ids: list[int] = []
    for genre_data in details.get("genres", []):
        if not isinstance(genre_data, dict) or not isinstance(genre_data.get("id"), int):
            continue
        external_id = int(genre_data["id"])
        genre = await genre_repo.get_or_create(
            source="tmdb",
            external_id=external_id,
            media_type=str(media_type),
            name=genre_names.get(external_id) or str(genre_data.get("name") or external_id),
            update_name=external_id in genre_names,
        )
        genre_ids.append(genre.id)
    await media_repo.replace_genres(media_id=media.id, genre_ids=genre_ids)
    return media


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


def _translation_language(locale: str) -> str:
    return "ru-RU" if locale == "ru" else "en-US"
