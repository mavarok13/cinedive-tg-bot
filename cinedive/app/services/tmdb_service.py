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

    async def discover_media(
        self,
        *,
        media_type: str,
        language: str,
        genre_ids: set[int],
        max_runtime_minutes: int | None,
        page: int = 1,
        sort_by: str = "vote_average.desc",
    ) -> list[dict[str, Any]]:
        if media_type not in {"movie", "tv"}:
            raise ValueError("media_type must be 'movie' or 'tv'.")

        date_key = "primary_release_date.gte" if media_type == "movie" else "first_air_date.gte"
        params: dict[str, Any] = {
            "language": language,
            "include_adult": "false",
            "include_video": "false",
            "page": page,
            "sort_by": sort_by,
            "vote_average.gte": 6.0,
            "vote_count.gte": 100,
            date_key: "1990-01-01",
        }
        if genre_ids:
            params["with_genres"] = "|".join(str(genre_id) for genre_id in sorted(genre_ids))
        if max_runtime_minutes is not None:
            params["with_runtime.lte"] = max_runtime_minutes

        data = await self._get(f"/discover/{media_type}", params=params)
        return list(data.get("results", []))

    async def get_genres(self, media_type: str, language: str) -> list[dict[str, Any]]:
        if media_type not in {"movie", "tv"}:
            raise ValueError("media_type must be 'movie' or 'tv'.")
        data = await self._get(f"/genre/{media_type}/list", params={"language": language})
        return list(data.get("genres", []))

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        response = await self._client.get(path, params={**params, "api_key": self._api_key})
        response.raise_for_status()
        return response.json()
