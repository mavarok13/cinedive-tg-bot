from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from cinedive.app.localization import t


def search_results_keyboard(results: list[dict[str, object]], locale: str | None = None) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    for index, result in enumerate(results, start=1):
        title = str(result.get("title") or t(locale, "search.unknown_title"))
        year = result.get("year")
        media_type = result.get("media_type")
        type_label = t(locale, f"media_types.{media_type}")
        suffix = f" ({year})" if year else ""
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{index}. {title}{suffix} - {type_label}"[:64],
                    callback_data=f"search:select:{index - 1}",
                )
            ]
        )
    buttons.append([InlineKeyboardButton(text=t(locale, "navigation.back"), callback_data="menu:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
