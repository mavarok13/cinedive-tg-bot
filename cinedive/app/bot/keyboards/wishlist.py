from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from cinedive.app.database.repositories.media_repository import MediaCardData
from cinedive.app.localization import t


def wishlist_keyboard(items: list[MediaCardData], locale: str | None = None) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    for index, item in enumerate(items, start=1):
        year = f" ({item.release_year})" if item.release_year else ""
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{index}. {item.title}{year}"[:64],
                    callback_data=f"wishlist:open:{item.id}",
                )
            ]
        )
    buttons.append([InlineKeyboardButton(text=t(locale, "navigation.back"), callback_data="menu:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
