from dataclasses import dataclass
from typing import Any
from urllib.parse import quote_plus

import httpx


@dataclass(frozen=True)
class SoundtrackLink:
    source: str
    title: str
    external_url: str
    direct: bool = False


class SoundtrackService:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=10.0)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def resolve_links(self, *, title: str, year: int | None = None) -> list[SoundtrackLink]:
        direct_link = await self.resolve_deezer_link(title=title, year=year)
        links = self.platform_search_links(title=title, year=year)
        return ([direct_link] if direct_link is not None else []) + links

    async def resolve_deezer_link(
        self,
        *,
        title: str,
        year: int | None = None,
    ) -> SoundtrackLink | None:
        query = f"{title} {year} soundtrack" if year else f"{title} soundtrack"
        response = await self._client.get(
            "https://api.deezer.com/search/album",
            params={"q": query, "limit": 5},
        )
        response.raise_for_status()
        data = response.json()
        for item in data.get("data", []):
            if not isinstance(item, dict) or not _is_confident_deezer_match(item, title):
                continue
            url = item.get("link")
            link_title = item.get("title") or query
            if isinstance(url, str):
                return SoundtrackLink(
                    source="deezer",
                    title=str(link_title),
                    external_url=url,
                    direct=True,
                )
        return None

    def platform_search_links(self, *, title: str, year: int | None = None) -> list[SoundtrackLink]:
        query = f"{title} {year} soundtrack" if year else f"{title} soundtrack"
        encoded = quote_plus(query)
        return [
            SoundtrackLink(
                source="deezer_search",
                title=query,
                external_url=f"https://www.deezer.com/search/{encoded}",
            ),
            SoundtrackLink(
                source="youtube_music",
                title=query,
                external_url=f"https://music.youtube.com/search?q={encoded}",
            ),
            SoundtrackLink(
                source="spotify",
                title=query,
                external_url=f"https://open.spotify.com/search/{encoded}",
            ),
            SoundtrackLink(
                source="apple_music",
                title=query,
                external_url=f"https://music.apple.com/search?term={encoded}",
            ),
            SoundtrackLink(
                source="yandex_music",
                title=query,
                external_url=f"https://music.yandex.com/search?text={encoded}",
            ),
        ]


def _is_confident_deezer_match(item: dict[str, Any], title: str) -> bool:
    album_title = str(item.get("title") or "").lower()
    media_title = title.lower()
    return "soundtrack" in album_title and any(part in album_title for part in media_title.split())
