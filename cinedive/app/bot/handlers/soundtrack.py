import httpx
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from cinedive.app.database.models import Soundtrack
from cinedive.app.database.repositories import MediaRepository, SoundtrackRepository
from cinedive.app.localization import t, user_locale
from cinedive.app.services.soundtrack_service import SoundtrackService
from cinedive.app.utils.formatting import html_escape

router = Router(name="soundtrack")


@router.callback_query(F.data.startswith("soundtrack:"))
async def soundtrack_link(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()

    locale = user_locale(callback.from_user)
    if not isinstance(callback.message, Message):
        return

    media_id = _media_id_from_callback(callback.data)
    if media_id is None:
        await callback.message.answer(t(locale, "soundtrack.invalid_media"))
        return

    media = await MediaRepository(session).get_card(
        media_id=media_id,
        language_code=_translation_language(locale),
    )
    if media is None:
        await callback.message.answer(t(locale, "soundtrack.invalid_media"))
        return

    repository = SoundtrackRepository(session)
    links = await repository.list_by_media_id(media_id)
    if not links:
        service = SoundtrackService()
        try:
            resolved_links = await service.resolve_links(title=media.title, year=media.release_year)
        except httpx.HTTPError:
            resolved_links = service.platform_search_links(title=media.title, year=media.release_year)
        finally:
            await service.aclose()
        for link in resolved_links:
            await repository.upsert(
                media_id=media_id,
                title=link.title,
                source=link.source,
                external_url=link.external_url,
            )
        await session.commit()
        links = await repository.list_by_media_id(media_id)

    await callback.message.answer(_soundtrack_text(media.title, links, locale), disable_web_page_preview=True)


def _soundtrack_text(title: str, links: list[Soundtrack], locale: str) -> str:
    lines = [t(locale, "soundtrack.title", title=html_escape(title)), t(locale, "soundtrack.disclaimer")]
    for link in links:
        label = t(locale, f"soundtrack.platforms.{link.source}")
        lines.append(f'<a href="{html_escape(link.external_url)}">{html_escape(label)}</a>')
    return "\n".join(lines)


def _media_id_from_callback(callback_data: str | None) -> int | None:
    if callback_data is None:
        return None
    try:
        return int(callback_data.rsplit(":", maxsplit=1)[1])
    except (IndexError, ValueError):
        return None


def _translation_language(locale: str) -> str:
    return "ru-RU" if locale == "ru" else "en-US"
