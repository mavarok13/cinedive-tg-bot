# Setup

## Required APIs

- Telegram: create a bot with BotFather and copy the bot token to `BOT_TOKEN`.
- TMDB: create a TMDB account, open `Settings` -> `API`, copy the v3 `API Key`, and set `TMDB_API_KEY`.
- Use the TMDB API Key, not the v4 API Read Access Token.

## Optional APIs

- Deezer: no key is required for the current soundtrack MVP. The bot uses Deezer public search API for a direct soundtrack match when available.
- Spotify, Apple Music, YouTube Music, and Yandex Music: no keys are required for the current MVP because the bot returns legal search links for these platforms.

## Local Run

- Set `BOT_MODE=polling`.
- Set `BOT_TOKEN`, `DATABASE_URL`, and `TMDB_API_KEY`.
- Start PostgreSQL and run `alembic upgrade head`.
- Run `python -m cinedive.app.main`.

## Production Webhook

- Set `APP_ENV=production`.
- Set `BOT_MODE=webhook`.
- Set `WEBHOOK_BASE_URL` to the public HTTPS base URL.
- Set `WEBHOOK_PATH`, default `/telegram/webhook`.
- Set `WEBHOOK_SECRET` to a long random value.
- Set `WEB_SERVER_HOST` and `WEB_SERVER_PORT` for the aiohttp server behind the reverse proxy.

## GitHub Actions Deploy Secrets

- `DEPLOY_HOST`: remote host.
- `DEPLOY_SSH_KEY`: private key for SSH deployment.
- `POSTGRES_APP_PASSWORD`: application database role password.
- `POSTGRES_SUPERUSER_PASSWORD`: PostgreSQL bootstrap superuser password.
- `DEPLOY_PORT`: optional SSH port, defaults to `22`.
- `GHCR_USERNAME` and `GHCR_READ_TOKEN`: optional, only needed when the server cannot pull GHCR anonymously.

The remote `.env` must contain runtime secrets such as `BOT_TOKEN`, `TMDB_API_KEY`, `WEBHOOK_BASE_URL`, and `WEBHOOK_SECRET`.
