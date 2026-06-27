from aiogram import F, Router
from aiogram.types import CallbackQuery

from cinedive.app.localization import t, user_locale

router = Router(name="soundtrack")


@router.callback_query(F.data.startswith("soundtrack:"))
async def soundtrack_link(callback: CallbackQuery) -> None:
    locale = user_locale(callback.from_user)
    await callback.answer(t(locale, "soundtrack.placeholder"), show_alert=True)
