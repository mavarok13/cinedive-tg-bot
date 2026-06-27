# Last Changes

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
