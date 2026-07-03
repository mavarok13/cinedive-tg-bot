from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def rating_keyboard(media_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=str(value), callback_data=f"rating:set:{media_id}:{value}")
                for value in range(1, 6)
            ],
            [
                InlineKeyboardButton(text=str(value), callback_data=f"rating:set:{media_id}:{value}")
                for value in range(6, 11)
            ],
        ]
    )
