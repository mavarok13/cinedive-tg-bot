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
- Deezer public API for optional direct soundtrack link resolution.
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
- `MOOD_SESSION_TTL_HOURS`: mood session lifetime, default `24`.
- `BOT_MODE`: `webhook` or `polling`. Production `APP_ENV=production` requires `webhook`.
- `WEBHOOK_BASE_URL`: public HTTPS base URL used to register the Telegram webhook.
- `WEBHOOK_PATH`: webhook path served by aiohttp, default `/telegram/webhook`.
- `WEBHOOK_SECRET`: secret passed to Telegram as `secret_token` and validated on inbound webhook requests.
- `WEB_SERVER_HOST`: aiohttp bind host, default `0.0.0.0`.
- `WEB_SERVER_PORT`: aiohttp bind port, default `8080`.
- `BOT_IMAGE`: Docker image used by Docker Compose, set by deployment to the GHCR `latest` tag.

Docker Compose PostgreSQL variables:

- `POSTGRES_DB`: database name.
- `POSTGRES_PORT`: local host port for PostgreSQL, default `5432`.
- `POSTGRES_APP_USER`: non-superuser application database role, default `cinedive_bot_app`.
- `POSTGRES_APP_PASSWORD`: application database role password.
- `POSTGRES_SUPERUSER_PASSWORD`: bootstrap password for the `postgres` superuser inside the PostgreSQL container.

## Deployment

- `Dockerfile` packages the Python app with `pip install .`.
- `docker-compose.yml` starts PostgreSQL and the bot service from `BOT_IMAGE`, binding PostgreSQL and the webhook port to localhost for reverse-proxy usage.
- `deploy/postgres/init/01-create-app-database.sh` creates or updates the non-superuser app database role and database on first PostgreSQL volume initialization.
- `.github/workflows/deploy.yml` builds and pushes `ghcr.io/<owner>/<repo>`, copies compose/bootstrap files to `/home/deploy/apps/cinedive-tg-bot`, updates remote deployment variables, runs `alembic upgrade head`, and restarts Docker Compose.
- Production deployments must set `BOT_MODE=webhook`, `APP_ENV=production`, and provide a public HTTPS `WEBHOOK_BASE_URL`.
- Required GitHub Actions secrets are `DEPLOY_HOST`, `DEPLOY_SSH_KEY`, `POSTGRES_APP_PASSWORD`, and `POSTGRES_SUPERUSER_PASSWORD`; `DEPLOY_PORT`, `GHCR_READ_TOKEN`, and `GHCR_USERNAME` are optional.
- The remote `.env` must contain runtime secrets such as `BOT_TOKEN`, `TMDB_API_KEY`, `WEBHOOK_BASE_URL`, and `WEBHOOK_SECRET`.
- Soundtrack links do not require additional secrets in the current MVP.

## Verification Notes

- `python -m compileall cinedive alembic` is the lightest syntax check.
- `ruff check .` is appropriate when dev dependencies are installed.
- `alembic upgrade head` requires a configured `.env` and reachable PostgreSQL database.
