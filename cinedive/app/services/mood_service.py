from datetime import UTC, datetime, timedelta

from cinedive.app.config import Settings, get_settings


class MoodService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def expires_at(self, now: datetime | None = None) -> datetime:
        current = now or datetime.now(UTC)
        return current + timedelta(hours=self._settings.mood_session_ttl_hours)

    def is_expired(self, expires_at: datetime, now: datetime | None = None) -> bool:
        current = now or datetime.now(UTC)
        return expires_at <= current
