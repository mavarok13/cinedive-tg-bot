# CineDive Telegram Bot

CineDive is a Telegram bot for movie and TV show recommendations. Users will be able to search TMDB media, add titles to a wishlist, mark them as watched, rate them, and receive simple recommendations based on favorite genres and temporary mood preferences.

## Current MVP Stage

- Clean modular project skeleton.
- aiogram 3 app with production webhook mode and optional local polling.
- PostgreSQL connection with SQLAlchemy 2 async.
- Alembic initial schema migration.
- `/start` user registration.
- Favorite-genre onboarding.
- Main menu and profile summary.
- English/Russian UI localization from packaged YAML locale files.
- TMDB async client scaffold.

Search, media cards, wishlist actions, watched/rating, recommendations, mood sessions, and soundtrack links are intentionally staged for follow-up work.

## Project Layout

```text
cinedive/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── bot/
│   ├── database/
│   ├── services/
│   └── utils/
├── lang/
├── alembic/
├── deploy/
├── .github/workflows/
├── docs/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── .env.example
```

## Quick Start

1. Install dependencies with `uv sync --extra dev` or `pip install -e .[dev]`.
2. Copy `.env.example` to `.env` and fill `BOT_TOKEN`, `DATABASE_URL`, and `TMDB_API_KEY`.
3. Start PostgreSQL with `docker compose up -d postgres` if using the provided compose file.
4. Apply migrations with `alembic upgrade head`.
5. For local development, set `BOT_MODE=polling` and run `python -m cinedive.app.main`.

## Production Webhook Mode

Production must use `BOT_MODE=webhook`. Set these variables before running the app:

- `WEBHOOK_BASE_URL`, for example `https://bot.example.com`.
- `WEBHOOK_PATH`, for example `/telegram/webhook`.
- `WEBHOOK_SECRET`, a long random value used as Telegram `secret_token`.
- `WEB_SERVER_HOST`, usually `0.0.0.0`.
- `WEB_SERVER_PORT`, usually `8080` behind a reverse proxy.

Webhook mode starts an aiohttp server, registers the Telegram webhook on startup, validates Telegram webhook secret headers, and exposes `GET /health`.

## GitHub Actions Deployment

`.github/workflows/deploy.yml` deploys on pushes to `main` and manual `workflow_dispatch` runs. It builds and pushes `ghcr.io/<owner>/<repo>`, copies `docker-compose.yml` and the PostgreSQL init script to `/home/deploy/apps/cinedive-tg-bot`, updates deployment variables in the remote `.env`, runs `alembic upgrade head`, and restarts Docker Compose.

Required GitHub secrets:

- `DEPLOY_HOST`
- `DEPLOY_SSH_KEY`
- `POSTGRES_APP_PASSWORD`
- `POSTGRES_SUPERUSER_PASSWORD`

Optional GitHub secrets:

- `DEPLOY_PORT`, defaults to `22`.
- `GHCR_READ_TOKEN` and `GHCR_USERNAME`, only needed if the server cannot pull the GHCR image anonymously.

The remote `.env` must also contain bot runtime secrets such as `BOT_TOKEN`, `TMDB_API_KEY`, `WEBHOOK_BASE_URL`, and `WEBHOOK_SECRET`. The workflow manages `BOT_IMAGE`, `APP_ENV=production`, `BOT_MODE=webhook`, and PostgreSQL deployment variables.

## Architecture Rules

- `handlers` handle Telegram UX only.
- `services` contain business logic and external API integrations.
- `repositories` contain database access.
- `models` contain SQLAlchemy models.
- `tmdb_service` is the only TMDB API integration point.
- Party/match features, ML recommendations, and music-file delivery are out of scope for the MVP.

## License

Copyright © 2026 Samuil Makarov. All rights reserved.

This project is proprietary and source-available for portfolio/review purposes only.  
You may not copy, modify, distribute, monetize, deploy, or create derivative works based on this project without prior written permission.
