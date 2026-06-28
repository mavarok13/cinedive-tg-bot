# Changelogs

## 2026-06-28

- Implemented Stage 4 recommendations in `cinedive/app/bot/handlers/recommendations.py`, including mood preset selection, active mood-session reuse, Next, and temporary Hide callbacks.
- Added `cinedive/app/bot/keyboards/mood.py` and expanded `MoodService`, `MediaRepository`, `UserMediaRepository`, and `RecommendationService` for 24-hour mood sessions, recommendation candidates, temporary hidden exclusions, and non-ML scoring.
- Updated `MOOD_SESSION_TTL_HOURS` default and `.env.example` from 48 to 24 hours.
- Updated localized English/Russian copy, README, AGENTS, and persistent docs for Stage 4 completion.
- Verification: `py -3.11 -m compileall cinedive alembic`, `pyproject.toml` TOML parse check, and `git diff --check` passed. Ruff was not available locally, so lint verification was skipped.

## 2026-06-28

- Implemented Stage 3 wishlist, watched, and rating flows in `cinedive/app/bot/handlers/wishlist.py` and `cinedive/app/bot/handlers/rating.py`.
- Added reusable persisted media-card rendering in `cinedive/app/bot/media_cards.py` plus wishlist and rating inline keyboards.
- Extended `MediaRepository` and `UserMediaRepository` to support persisted card loading, wishlist removal, watched status, ratings, and `rated_at` persistence through existing schema.
- Updated localized English/Russian copy, README, AGENTS, and persistent docs for Stage 3 completion.
- Verification: `py -3.11 -m compileall cinedive alembic`, `pyproject.toml` TOML parse check, and `git diff --check` passed. Handler import smoke test was blocked because `aiogram` is not installed in the local Python 3.11 environment. Ruff was not available locally, so lint verification was skipped.

## 2026-06-28

- Updated `AGENTS.md`, `docs/INFO.md`, `docs/ROADMAP.md`, and `docs/ARCHITECTURE.md` to define soundtrack behavior as legal external music-platform links rather than audio delivery.
- Clarified that future soundtrack integrations may use official/public APIs to resolve direct platform links, should fall back to platform search links when confidence is low, and must not download, proxy, upload, cache, or send music files.
- Verification: documentation-only change; no runtime checks were run.

## 2026-06-28

- Implemented `cinedive/app/bot/handlers/search.py` so the Search menu button starts an FSM query flow, calls `TMDBService.search_media`, renders inline result choices, fetches selected movie/TV details, and sends localized media cards with poster fallback behavior.
- Updated `cinedive/app/bot/handlers/menu.py` to clear FSM state when users return to the main menu or press Back.
- Added `cinedive/app/bot/keyboards/search.py` for result-choice inline keyboards and expanded search/media-card locale keys in `cinedive/lang/en.yml` and `cinedive/lang/ru.yml`.
- Extended repository support in `MediaRepository` and `GenreRepository` so selected media persist media items, translations, canonical genre records, and media-genre links without moving SQLAlchemy logic into handlers.
- Updated README and persistent docs for Stage 2 completion.
- Verification: `py -3.11 -m compileall cinedive alembic`, `pyproject.toml` TOML parse check, and `git diff --check` passed. Ruff was not available locally, so lint verification was skipped.

## 2026-06-27

- Added `.github/workflows/deploy.yml` for GHCR image publishing and remote Docker Compose deployment modeled after the sibling Telegram bot project.
- Updated `docker-compose.yml` to consume `BOT_IMAGE`, bind PostgreSQL and webhook ports to localhost, and run PostgreSQL with a bootstrap superuser plus non-superuser CineDive app role.
- Added `deploy/postgres/init/01-create-app-database.sh` to create or update the app role and database during PostgreSQL initialization.
- Added `.dockerignore`, updated `.env.example`, README, and persistent docs with deployment variables, required GitHub secrets, and Alembic migration behavior.
- Verification: `py -3.11 -m compileall cinedive alembic`, `pyproject.toml` TOML parse check, `docker compose config` with a temporary `.env`, and `git diff --check` passed. Ruff was not available locally, so lint verification was skipped.

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
