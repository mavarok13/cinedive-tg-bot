from aiogram import F, Router
from aiogram.types import CallbackQuery

from cinedive.app.localization import t, user_locale

router = Router(name="rating")


@router.callback_query(F.data.startswith("rate:"))
async def rate_media(callback: CallbackQuery) -> None:
    locale = user_locale(callback.from_user)
    await callback.answer(t(locale, "rating.placeholder"), show_alert=True)


@router.callback_query(F.data.startswith("watched:"))
async def mark_watched(callback: CallbackQuery) -> None:
    locale = user_locale(callback.from_user)
    await callback.answer(t(locale, "watched.placeholder"), show_alert=True)
