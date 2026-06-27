from urllib.parse import quote_plus


class SoundtrackService:
    def build_youtube_search_url(self, *, title: str, year: int | None = None) -> str:
        query = f"{title} {year} soundtrack" if year else f"{title} soundtrack"
        return f"https://www.youtube.com/results?search_query={quote_plus(query)}"
