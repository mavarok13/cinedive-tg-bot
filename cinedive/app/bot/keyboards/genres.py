from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from cinedive.app.localization import DEFAULT_LOCALE, t

POPULAR_MOVIE_GENRES: tuple[tuple[int, str], ...] = (
    (28, "action"),
    (12, "adventure"),
    (16, "animation"),
    (35, "comedy"),
    (80, "crime"),
    (18, "drama"),
    (14, "fantasy"),
    (27, "horror"),
    (9648, "mystery"),
    (10749, "romance"),
    (878, "sci_fi"),
    (53, "thriller"),
)


def canonical_genre_name(external_id: int) -> str | None:
    for genre_id, locale_key in POPULAR_MOVIE_GENRES:
        if genre_id == external_id:
            return t(DEFAULT_LOCALE, f"genres.movie.{locale_key}")
    return None


def genre_display_name(locale: str | None, external_id: int) -> str | None:
    for genre_id, locale_key in POPULAR_MOVIE_GENRES:
        if genre_id == external_id:
            return t(locale, f"genres.movie.{locale_key}")
    return None


def favorite_genres_keyboard(
    selected_external_ids: set[int], locale: str | None = None
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for external_id, locale_key in POPULAR_MOVIE_GENRES:
        marker = "✅" if external_id in selected_external_ids else "▫️"
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{marker} {t(locale, f'genres.movie.{locale_key}')}",
                    callback_data=f"genre:{external_id}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text=t(locale, "onboarding.done"), callback_data="genre_done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
