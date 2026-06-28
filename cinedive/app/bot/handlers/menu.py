from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from cinedive.app.bot.keyboards import is_back_button_text, main_menu_keyboard
from cinedive.app.localization import t, user_locale

router = Router(name="menu")


@router.message(Command("menu"))
async def menu_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    locale = user_locale(message.from_user)
    await message.answer(t(locale, "menu.title"), reply_markup=main_menu_keyboard(locale))


@router.message(F.text.func(is_back_button_text))
async def back_to_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    locale = user_locale(message.from_user)
    await message.answer(t(locale, "menu.title"), reply_markup=main_menu_keyboard(locale))


@router.callback_query(F.data == "menu:back")
async def back_to_menu_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    if isinstance(callback.message, Message):
        locale = user_locale(callback.from_user)
        await callback.message.answer(t(locale, "menu.title"), reply_markup=main_menu_keyboard(locale))
