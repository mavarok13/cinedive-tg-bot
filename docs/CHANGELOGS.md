# Changelogs

## 2026-06-27

- Added `cinedive/app/localization.py` and packaged `cinedive/lang/en.yml` / `cinedive/lang/ru.yml` for YAML-backed UI localization.
- Updated bot handlers and keyboard builders to render menu labels, onboarding copy, profile text, placeholder responses, callback alerts, media-card buttons, and genre labels from locale files using Telegram `language_code`.
- Kept genre persistence canonical by continuing to store English TMDB genre names while displaying localized genre labels in the UI.
- Added `PyYAML` to `pyproject.toml` for YAML parsing and updated README/context docs for the localization architecture.
- Verification: `py -3.11 -m compileall cinedive alembic` and a `pyproject.toml` TOML parse check passed. Ruff was not available locally, so lint verification was skipped. A direct localization import smoke test was blocked because the local Python 3.11 environment does not have the newly declared `PyYAML` dependency installed yet.

## 2026-06-27

- Refactored `cinedive/app/main.py` so production can run as an aiohttp webhook server instead of long polling.
- Added `BOT_MODE`, webhook URL/path/secret, and web server host/port settings in `cinedive/app/config.py` and `.env.example`.
- Added Telegram webhook registration with `secret_token`, inbound secret validation through aiogram's aiohttp webhook handler, and `GET /health`.
- Kept polling only as an explicit local mode behind `BOT_MODE=polling` and prevented polling with `APP_ENV=production`.
- Updated callback query handlers to acknowledge before database work or message edits.
- Updated README and persistent docs for the webhook architecture.
- Verification: `py -3.11 -m compileall cinedive alembic` and a `pyproject.toml` TOML parse check passed. Ruff was not available locally, so lint verification was skipped.

## 2026-06-27

- Initialized the Python aiogram project skeleton for CineDive.
- Added clean architecture directories for bot handlers/keyboards/states/middlewares, database models/repositories, services, and utilities.
- Added PostgreSQL SQLAlchemy models and Alembic initial migration for users, genres, media, user media state, mood sessions, and soundtracks.
- Implemented `/start` user registration, favorite-genre onboarding, main menu, and a basic profile response.
- Added a reusable async TMDB client with search, movie details, TV details, and genres methods.
- Added Docker, Compose, environment example, README updates, and persistent AI guidance docs.
- Verification: `py -3.11 -m compileall cinedive alembic` and a `pyproject.toml` TOML parse check passed. Ruff was not available locally, so lint verification was skipped.
