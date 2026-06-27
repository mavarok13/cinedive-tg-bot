from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from cinedive.app.localization import t, text_variants


def is_menu_button_text(text: str | None, action: str) -> bool:
    if text is None:
        return False
    return text in text_variants(f"menu.buttons.{action}")


def is_back_button_text(text: str | None) -> bool:
    if text is None:
        return False
    return text in text_variants("navigation.back")


def main_menu_keyboard(locale: str | None = None) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t(locale, "menu.buttons.recommend")),
                KeyboardButton(text=t(locale, "menu.buttons.wishlist")),
            ],
            [
                KeyboardButton(text=t(locale, "menu.buttons.search")),
                KeyboardButton(text=t(locale, "menu.buttons.profile")),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder=t(locale, "menu.placeholder"),
    )
