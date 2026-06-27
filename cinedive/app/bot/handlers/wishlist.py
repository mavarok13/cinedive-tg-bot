from aiogram import F, Router
from aiogram.types import Message

from cinedive.app.bot.keyboards import is_menu_button_text
from cinedive.app.localization import t, user_locale

router = Router(name="wishlist")


@router.message(F.text.func(lambda text: is_menu_button_text(text, "wishlist")))
async def wishlist_entry(message: Message) -> None:
    locale = user_locale(message.from_user)
    await message.answer(t(locale, "wishlist.placeholder"))
