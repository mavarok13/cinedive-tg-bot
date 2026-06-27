from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from cinedive.app.bot.keyboards import is_menu_button_text
from cinedive.app.bot.states import SearchStates
from cinedive.app.localization import t, user_locale

router = Router(name="search")


@router.message(F.text.func(lambda text: is_menu_button_text(text, "search")))
async def ask_search_query(message: Message, state: FSMContext) -> None:
    await state.set_state(SearchStates.waiting_query)
    locale = user_locale(message.from_user)
    await message.answer(t(locale, "search.ask_query"))


@router.message(SearchStates.waiting_query)
async def receive_search_query(message: Message, state: FSMContext) -> None:
    await state.clear()
    locale = user_locale(message.from_user)
    await message.answer(t(locale, "search.placeholder"))
