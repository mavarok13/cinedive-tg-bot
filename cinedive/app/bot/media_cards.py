from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

from cinedive.app.bot.keyboards import media_card_keyboard
from cinedive.app.bot.keyboards.genres import genre_display_name
from cinedive.app.config import Settings
from cinedive.app.database.repositories.media_repository import MediaCardData
from cinedive.app.localization import t
from cinedive.app.utils.formatting import html_escape

MAX_OVERVIEW_LENGTH = 650


async def send_media_card(
    message: Message,
    card: MediaCardData,
    settings: Settings,
    locale: str,
    *,
    in_wishlist: bool = False,
) -> None:
    text = media_card_text(card, locale)
    reply_markup = media_card_keyboard(card.id, locale, in_wishlist=in_wishlist)
    poster_url = _poster_url(card.poster_path, settings)
    if poster_url is None:
        await message.answer(text, reply_markup=reply_markup)
        return

    try:
        await message.answer_photo(photo=poster_url, caption=text, reply_markup=reply_markup)
    except TelegramBadRequest:
        await message.answer(text, reply_markup=reply_markup)


def media_card_text(card: MediaCardData, locale: str) -> str:
    lines = [f"<b>{html_escape(card.title)}</b>", t(locale, f"media_types.{card.media_type}")]
    if card.release_year:
        lines[-1] = f"{lines[-1]} - {card.release_year}"
    if card.origin_country:
        lines.append(t(locale, "media_card.country", country=html_escape(card.origin_country)))
    genres = _genre_names(card, locale)
    if genres:
        lines.append(t(locale, "media_card.genres", genres=html_escape(", ".join(genres))))
    if card.tmdb_rating is not None:
        lines.append(
            t(
                locale,
                "media_card.tmdb_rating",
                rating=f"{card.tmdb_rating:.1f}",
                votes=card.tmdb_vote_count or 0,
            )
        )
    if card.runtime_minutes:
        lines.append(t(locale, "media_card.runtime", minutes=card.runtime_minutes))
    overview = _truncated_overview(card.overview or "")
    if overview:
        lines.extend(["", html_escape(overview)])
    return "\n".join(lines)


def _poster_url(poster_path: str | None, settings: Settings) -> str | None:
    if not poster_path:
        return None
    return f"{settings.tmdb_image_base_url.rstrip('/')}/{poster_path.lstrip('/')}"


def _truncated_overview(overview: str) -> str:
    if len(overview) <= MAX_OVERVIEW_LENGTH:
        return overview
    return f"{overview[:MAX_OVERVIEW_LENGTH].rsplit(' ', maxsplit=1)[0]}..."


def _genre_names(card: MediaCardData, locale: str) -> list[str]:
    names: list[str] = []
    for external_id, fallback_name in card.genres:
        names.append(genre_display_name(locale, external_id) or fallback_name)
    return names
