# Last Changes

## 2026-06-28

- Implemented Stage 4.5 hybrid recommendation expansion.
- Added TMDB Discover candidate sourcing, persisted discovered media before ranking, stronger exclusion of watched/ignored/hidden/already-rated media, and collaborative rating boost from similar users when enough ratings exist.
- Kept IMDb as an external identifier only; recommendations continue to use TMDB/public app data and do not scrape IMDb or unofficial APIs.

Verification: `py -3.11 -m compileall cinedive alembic`, `pyproject.toml` TOML parse check, and `git diff --check` passed. `py -3.11 -m ruff check .` was skipped because Ruff is not installed in the local Python 3.11 environment.

## 2026-06-28

- Implemented Stage 4 mood sessions and simple recommendations.
- Added 24-hour mood presets, active mood session persistence, recommendation candidate loading from persisted media, non-ML scoring, Next, and temporary Hide behavior.
- Updated `MOOD_SESSION_TTL_HOURS` default/docs from 48 to 24 hours to match the roadmap.
- Updated English/Russian UI copy and persistent docs for Stage 4 completion.

Verification: `py -3.11 -m compileall cinedive alembic`, `pyproject.toml` TOML parse check, and `git diff --check` passed. `py -3.11 -m ruff check .` was skipped because Ruff is not installed in the local Python 3.11 environment.

## 2026-06-28

- Implemented Stage 3 wishlist, watched, and rating flows.
- Added reusable persisted media-card rendering, wishlist/rating inline keyboards, wishlist add/list/open/remove handlers, and watched/rating FSM handlers.
- Extended repositories to load persisted media-card data, delete user-media rows, and save watched ratings with `rated_at`.
- Updated English/Russian UI copy and persistent docs for Stage 3 completion while preserving soundtrack platform-link guidance.

Verification: `py -3.11 -m compileall cinedive alembic`, `pyproject.toml` TOML parse check, and `git diff --check` passed. Handler import smoke test was blocked because `aiogram` is not installed in the local Python 3.11 environment. `py -3.11 -m ruff check .` was skipped because Ruff is not installed in the local Python 3.11 environment.

## 2026-06-28

- Clarified soundtrack guidance so future work returns links to legal external music platforms, allows official/public API link resolution, and falls back to platform search links when needed.
- Documented that soundtrack flows must not download, proxy, upload, cache, or send music files and may cache only metadata and external URLs.

Verification: documentation-only change; no runtime checks were run.

## 2026-06-28

- Implemented Stage 2 TMDB search: users can submit a query, choose movie or TV results, fetch details, and receive localized media cards with posters and action buttons.
- Persisted selected TMDB media items, localized translations, and media-genre links through repositories while preserving handler/service/database boundaries.
- Updated English/Russian locale copy and persistent docs for the completed Stage 2 scope.

Verification: `py -3.11 -m compileall cinedive alembic`, `pyproject.toml` TOML parse check, and `git diff --check` passed. `py -3.11 -m ruff check .` was skipped because Ruff is not installed in the local Python 3.11 environment.

## 2026-06-27

- Added GitHub Actions deployment that builds and pushes the bot image to GHCR, copies Compose/bootstrap files to the remote host, runs Alembic migrations, and restarts Docker Compose.
- Updated Docker Compose to run the bot from `BOT_IMAGE`, bind exposed services to localhost, and bootstrap PostgreSQL with a non-superuser app role.
- Added PostgreSQL init bootstrap and `.dockerignore`, and documented deployment secrets and runtime requirements.

Verification: `py -3.11 -m compileall cinedive alembic`, `pyproject.toml` TOML parse check, `docker compose config` with a temporary `.env`, and `git diff --check` passed. `py -3.11 -m ruff check .` was skipped because Ruff is not installed in the local Python 3.11 environment.

## 2026-06-27

- Added YAML-backed UI localization with packaged English and Russian locale files.
- Updated handlers and keyboard builders to render Telegram-facing copy by user Telegram locale with English fallback.
- Localized main menu, onboarding, profile, placeholders, media-card labels, alerts, and genre labels while keeping stored genre names canonical.
- Added `PyYAML` as the locale file parser dependency.

Verification: `py -3.11 -m compileall cinedive alembic` passed. `pyproject.toml` TOML parse check passed. `py -3.11 -m ruff check .` was skipped because Ruff is not installed in the local Python 3.11 environment. Direct localization import smoke test was blocked because `PyYAML` is not installed in the local Python 3.11 environment yet; dependency declaration was added to `pyproject.toml`.

## 2026-06-27

- Refactored startup to support `BOT_MODE=webhook` production mode and optional local `BOT_MODE=polling`.
- Added aiohttp webhook server wiring, Telegram webhook `secret_token`, webhook settings, and `GET /health`.
- Enforced `APP_ENV=production` to require webhook mode.
- Audited callback query handlers so they acknowledge before database work or message edits.

Verification: `py -3.11 -m compileall cinedive alembic` passed. `pyproject.toml` TOML parse check passed. `py -3.11 -m ruff check .` was skipped because Ruff is not installed in the local Python 3.11 environment.

## 2026-06-27

- Created the CineDive MVP skeleton with Python package layout under `cinedive/app/`.
- Added pydantic-settings configuration, Docker files, `.env.example`, and Python dependency metadata.
- Added SQLAlchemy async database setup, ORM models, repositories, Alembic config, and initial schema migration.
- Added aiogram middleware, keyboards, FSM states, handlers, `/start` registration, favorite-genre onboarding, profile summary, and main menu.
- Added TMDB, recommendation, mood, and soundtrack service scaffolding.
- Added repository guidance and docs for future agents.

Verification: `py -3.11 -m compileall cinedive alembic` passed. `py -3.11 -c "import tomllib; tomllib.load(open('pyproject.toml','rb')); print('pyproject ok')"` passed. `py -3.11 -m ruff check .` was skipped because Ruff is not installed in the local Python 3.11 environment.
