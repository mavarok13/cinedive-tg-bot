from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from cinedive.app.localization import t


def media_card_keyboard(
    media_id: int,
    locale: str | None = None,
    *,
    in_wishlist: bool = False,
) -> InlineKeyboardMarkup:
    wishlist_text = "media_card.remove_wishlist" if in_wishlist else "media_card.to_wishlist"
    wishlist_action = "remove" if in_wishlist else "add"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(locale, wishlist_text),
                    callback_data=f"wishlist:{wishlist_action}:{media_id}",
                ),
                InlineKeyboardButton(
                    text=t(locale, "media_card.watched"), callback_data=f"watched:{media_id}"
                ),
            ],
            [
                InlineKeyboardButton(text=t(locale, "media_card.rate"), callback_data=f"rate:{media_id}"),
                InlineKeyboardButton(
                    text=t(locale, "media_card.not_now"), callback_data=f"hide:{media_id}"
                ),
            ],
            [
                InlineKeyboardButton(text=t(locale, "media_card.next"), callback_data="recommend:next"),
                InlineKeyboardButton(
                    text=t(locale, "media_card.soundtrack"),
                    callback_data=f"soundtrack:{media_id}",
                ),
            ],
            [InlineKeyboardButton(text=t(locale, "navigation.back"), callback_data="menu:back")],
        ]
    )
