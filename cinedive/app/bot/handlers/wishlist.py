from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from cinedive.app.bot.keyboards import is_menu_button_text, wishlist_keyboard
from cinedive.app.bot.media_cards import send_media_card
from cinedive.app.config import get_settings
from cinedive.app.database.repositories import MediaRepository, UserMediaRepository, UserRepository
from cinedive.app.database.repositories.media_repository import MediaCardData
from cinedive.app.localization import t, user_locale
from cinedive.app.utils.formatting import html_escape

router = Router(name="wishlist")


@router.message(F.text.func(lambda text: is_menu_button_text(text, "wishlist")))
async def wishlist_entry(message: Message, session: AsyncSession) -> None:
    locale = user_locale(message.from_user)
    user = await UserRepository(session).get_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer(t(locale, "errors.use_start"))
        return

    cards = await _wishlist_cards(session, user.id, _translation_language(locale))
    if not cards:
        await message.answer(t(locale, "wishlist.empty"))
        return

    await message.answer(
        t(locale, "wishlist.title"),
        reply_markup=wishlist_keyboard(cards, locale),
    )


@router.callback_query(F.data.startswith("wishlist:add:"))
async def add_to_wishlist(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()

    locale = user_locale(callback.from_user)
    media_id = _media_id_from_callback(callback.data)
    if media_id is None:
        await _answer_message(callback, t(locale, "wishlist.invalid_media"))
        return

    user = await UserRepository(session).get_by_telegram_id(callback.from_user.id)
    if user is None:
        await _answer_message(callback, t(locale, "errors.use_start"))
        return

    card = await MediaRepository(session).get_card(
        media_id=media_id,
        language_code=_translation_language(locale),
    )
    if card is None:
        await _answer_message(callback, t(locale, "wishlist.invalid_media"))
        return

    await UserMediaRepository(session).set_status(user_id=user.id, media_id=media_id, status="wishlist")
    await session.commit()
    await _answer_message(callback, t(locale, "wishlist.added", title=html_escape(card.title)))


@router.callback_query(F.data.startswith("wishlist:open:"))
async def open_wishlist_item(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()

    locale = user_locale(callback.from_user)
    media_id = _media_id_from_callback(callback.data)
    if media_id is None or not isinstance(callback.message, Message):
        return

    user = await UserRepository(session).get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.message.answer(t(locale, "errors.use_start"))
        return

    user_media = await UserMediaRepository(session).get(user_id=user.id, media_id=media_id)
    if user_media is None or (user_media.status != "wishlist" and user_media.wishlist_at is None):
        await callback.message.answer(t(locale, "wishlist.not_in_wishlist"))
        return

    card = await MediaRepository(session).get_card(
        media_id=media_id,
        language_code=_translation_language(locale),
    )
    if card is None:
        await callback.message.answer(t(locale, "wishlist.invalid_media"))
        return

    await send_media_card(callback.message, card, get_settings(), locale, in_wishlist=True)


@router.callback_query(F.data.startswith("wishlist:remove:"))
async def remove_from_wishlist(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()

    locale = user_locale(callback.from_user)
    media_id = _media_id_from_callback(callback.data)
    if media_id is None:
        await _answer_message(callback, t(locale, "wishlist.invalid_media"))
        return

    user = await UserRepository(session).get_by_telegram_id(callback.from_user.id)
    if user is None:
        await _answer_message(callback, t(locale, "errors.use_start"))
        return

    await UserMediaRepository(session).remove(user_id=user.id, media_id=media_id)
    await session.commit()
    await _answer_message(callback, t(locale, "wishlist.removed"))


async def _wishlist_cards(
    session: AsyncSession,
    user_id: int,
    language_code: str,
) -> list[MediaCardData]:
    media_repo = MediaRepository(session)
    cards: list[MediaCardData] = []
    for item in await UserMediaRepository(session).list_wishlist(user_id=user_id):
        card = await media_repo.get_card(media_id=item.media_id, language_code=language_code)
        if card is not None:
            cards.append(card)
    return cards


def _media_id_from_callback(callback_data: str | None) -> int | None:
    if callback_data is None:
        return None
    try:
        return int(callback_data.rsplit(":", maxsplit=1)[1])
    except (IndexError, ValueError):
        return None


def _translation_language(locale: str) -> str:
    return "ru-RU" if locale == "ru" else "en-US"


async def _answer_message(callback: CallbackQuery, text: str) -> None:
    if isinstance(callback.message, Message):
        await callback.message.answer(text)
