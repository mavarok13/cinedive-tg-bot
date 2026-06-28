from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "local"
    bot_mode: Literal["polling", "webhook"] = "webhook"
    bot_token: SecretStr | None = None
    database_url: str = "postgresql+asyncpg://cinedive:cinedive@localhost:5432/cinedive"
    database_echo: bool = False
    tmdb_api_key: SecretStr | None = None
    tmdb_base_url: str = "https://api.themoviedb.org/3"
    tmdb_image_base_url: str = "https://image.tmdb.org/t/p/w500"
    default_language: str = "en-US"
    log_level: str = "INFO"
    mood_session_ttl_hours: int = Field(default=24, ge=1)
    webhook_base_url: str | None = None
    webhook_path: str = "/telegram/webhook"
    webhook_secret: SecretStr | None = None
    web_server_host: str = "0.0.0.0"
    web_server_port: int = Field(default=8080, ge=1, le=65535)

    @model_validator(mode="after")
    def validate_production_mode(self) -> "Settings":
        if self.app_env.lower() in {"prod", "production"} and self.bot_mode != "webhook":
            raise ValueError("Production APP_ENV requires BOT_MODE=webhook.")
        return self

    @property
    def normalized_webhook_path(self) -> str:
        return self.webhook_path if self.webhook_path.startswith("/") else f"/{self.webhook_path}"

    @property
    def webhook_url(self) -> str:
        return f"{self.require_webhook_base_url().rstrip('/')}{self.normalized_webhook_path}"

    def require_bot_token(self) -> str:
        if self.bot_token is None:
            raise RuntimeError("BOT_TOKEN is required to run the Telegram bot.")
        return self.bot_token.get_secret_value()

    def require_webhook_base_url(self) -> str:
        if not self.webhook_base_url:
            raise RuntimeError("WEBHOOK_BASE_URL is required when BOT_MODE=webhook.")
        return self.webhook_base_url

    def require_webhook_secret(self) -> str:
        if self.webhook_secret is None:
            raise RuntimeError("WEBHOOK_SECRET is required when BOT_MODE=webhook.")
        return self.webhook_secret.get_secret_value()

    def require_tmdb_api_key(self) -> str:
        if self.tmdb_api_key is None:
            raise RuntimeError("TMDB_API_KEY is required for TMDB API requests.")
        return self.tmdb_api_key.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    return Settings()
