from typing import Any

import httpx

from cinedive.app.config import Settings, get_settings


class TMDBService:
    def __init__(self, settings: Settings | None = None, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings or get_settings()
        self._api_key = self._settings.require_tmdb_api_key()
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=self._settings.tmdb_base_url.rstrip("/"),
            timeout=15.0,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def search_media(self, query: str, language: str) -> list[dict[str, Any]]:
        data = await self._get(
            "/search/multi",
            params={
                "query": query,
                "language": language,
                "include_adult": "false",
            },
        )
        return [
            item
            for item in data.get("results", [])
            if item.get("media_type") in {"movie", "tv"}
        ]

    async def get_movie_details(self, tmdb_id: int, language: str) -> dict[str, Any]:
        return await self._get(
            f"/movie/{tmdb_id}",
            params={"language": language, "append_to_response": "external_ids"},
        )

    async def get_tv_details(self, tmdb_id: int, language: str) -> dict[str, Any]:
        return await self._get(
            f"/tv/{tmdb_id}",
            params={"language": language, "append_to_response": "external_ids"},
        )

    async def get_genres(self, media_type: str, language: str) -> list[dict[str, Any]]:
        if media_type not in {"movie", "tv"}:
            raise ValueError("media_type must be 'movie' or 'tv'.")
        data = await self._get(f"/genre/{media_type}/list", params={"language": language})
        return list(data.get("genres", []))

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        response = await self._client.get(path, params={**params, "api_key": self._api_key})
        response.raise_for_status()
        return response.json()
