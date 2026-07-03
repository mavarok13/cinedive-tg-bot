from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from cinedive.app.localization import t
from cinedive.app.services.mood_service import MOOD_PRESETS


def mood_presets_keyboard(locale: str | None = None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    keys = list(MOOD_PRESETS)
    for index in range(0, len(keys), 2):
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(locale, f"mood.presets.{key}"),
                    callback_data=f"mood:preset:{key}",
                )
                for key in keys[index : index + 2]
            ]
        )
    rows.append([InlineKeyboardButton(text=t(locale, "navigation.back"), callback_data="menu:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
