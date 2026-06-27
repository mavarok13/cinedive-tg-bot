# Stack

Technical stack for `cinedive-tg-bot`.

## Language And Project Config

- Language: Python 3.11+.
- Package/dependency metadata: `pyproject.toml`.
- Recommended dependency workflow: `uv`.
- Runtime entry point: `python -m cinedive.app.main`.
- Bot modes: `BOT_MODE=webhook` for production and `BOT_MODE=polling` for local development only.
- Formatting/linting target: Ruff, configured in `pyproject.toml`.

## Python Dependencies

- `aiogram` 3 for Telegram bot polling, routing, keyboards, middleware, and FSM.
- `aiohttp` for the production webhook web server and `/health` endpoint.
- `SQLAlchemy` 2 async ORM for database models and sessions.
- `asyncpg` as the PostgreSQL async driver.
- `Alembic` for schema migrations.
- `httpx` for TMDB API requests.
- `pydantic-settings` for environment-based configuration.
- `PyYAML` for packaged YAML locale files.
- `python-dotenv` for local `.env` loading, including Alembic.

## Runtime Services

- Telegram Bot API.
- TMDB API.
- PostgreSQL 16 in Docker Compose by default.

## Runtime Configuration

Primary environment variables:

- `BOT_TOKEN`: Telegram bot token.
- `DATABASE_URL`: SQLAlchemy async PostgreSQL URL, for example `postgresql+asyncpg://cinedive:cinedive@localhost:5432/cinedive`.
- `TMDB_API_KEY`: TMDB API key.
- `TMDB_BASE_URL`: TMDB API base URL, default `https://api.themoviedb.org/3`.
- `TMDB_IMAGE_BASE_URL`: poster image base URL, default `https://image.tmdb.org/t/p/w500`.
- `DEFAULT_LANGUAGE`: default TMDB language, default `en-US`.
- `DATABASE_ECHO`: SQLAlchemy SQL echo flag.
- `LOG_LEVEL`: Python logging level.
- `MOOD_SESSION_TTL_HOURS`: mood session lifetime, default `48`.
- `BOT_MODE`: `webhook` or `polling`. Production `APP_ENV=production` requires `webhook`.
- `WEBHOOK_BASE_URL`: public HTTPS base URL used to register the Telegram webhook.
- `WEBHOOK_PATH`: webhook path served by aiohttp, default `/telegram/webhook`.
- `WEBHOOK_SECRET`: secret passed to Telegram as `secret_token` and validated on inbound webhook requests.
- `WEB_SERVER_HOST`: aiohttp bind host, default `0.0.0.0`.
- `WEB_SERVER_PORT`: aiohttp bind port, default `8080`.

Docker Compose PostgreSQL variables:

- `POSTGRES_DB`: database name.
- `POSTGRES_USER`: database user.
- `POSTGRES_PASSWORD`: database password.

## Deployment

- `Dockerfile` packages the Python app with `pip install .`.
- `docker-compose.yml` starts PostgreSQL and the bot service, exposing `WEB_SERVER_PORT` for webhook mode.
- Production deployments must set `BOT_MODE=webhook` and provide a public HTTPS `WEBHOOK_BASE_URL`.

## Verification Notes

- `python -m compileall cinedive alembic` is the lightest syntax check.
- `ruff check .` is appropriate when dev dependencies are installed.
- `alembic upgrade head` requires a configured `.env` and reachable PostgreSQL database.
