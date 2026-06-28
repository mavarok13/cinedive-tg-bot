from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from cinedive.app.config import Settings, get_settings


@dataclass(frozen=True)
class MoodPreset:
    key: str
    content_type: str
    genre_external_ids: tuple[int, ...]
    max_runtime_minutes: int | None = None
    company_type: str | None = None


MOOD_PRESETS: dict[str, MoodPreset] = {
    "balanced": MoodPreset(key="balanced", content_type="any", genre_external_ids=()),
    "fun": MoodPreset(key="fun", content_type="any", genre_external_ids=(12, 16, 35)),
    "intense": MoodPreset(key="intense", content_type="any", genre_external_ids=(28, 53, 80, 9648)),
    "cozy": MoodPreset(key="cozy", content_type="movie", genre_external_ids=(14, 35, 10749), max_runtime_minutes=130),
    "short": MoodPreset(key="short", content_type="movie", genre_external_ids=(), max_runtime_minutes=100),
    "series": MoodPreset(key="series", content_type="tv", genre_external_ids=(18, 35, 9648)),
}


class MoodService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def expires_at(self, now: datetime | None = None) -> datetime:
        current = now or datetime.now(UTC)
        return current + timedelta(hours=self._settings.mood_session_ttl_hours)

    def is_expired(self, expires_at: datetime, now: datetime | None = None) -> bool:
        current = now or datetime.now(UTC)
        return expires_at <= current

    def preset(self, key: str) -> MoodPreset | None:
        return MOOD_PRESETS.get(key)

    def mood_tags(self, preset: MoodPreset) -> dict[str, object]:
        return {
            "preset": preset.key,
            "genre_external_ids": list(preset.genre_external_ids),
        }
