# AGENTS.md

Repository guidance for future coding agents. Start here before changing code.

## Read Order

1. Read this file.
2. Read `docs/INFO.md` for the short project summary and current feature state.
3. Read `docs/STACK.md` for language, dependencies, runtime settings, and deployment notes.
4. Read `docs/ARCHITECTURE.md` for component boundaries and data flow.
5. Read `docs/ROADMAP.md` for planned work and known future directions.
6. Read `docs/LAST_CHANGES.md` and `docs/CHANGELOGS.md` before editing, so new work continues from the latest context.

This is useful, but not guaranteed automatically by every agent runtime. Agents that support repository instructions often auto-load `AGENTS.md`; agents that do not should be explicitly told to read it.

## Documentation Maintenance Rule

After any project change, update the context docs when relevant:

- Update `docs/INFO.md` if user-visible features, behavior, requirements, or known limitations change.
- Update `docs/STACK.md` if language version, dependencies, deployment, environment variables, or infrastructure change.
- Update `docs/ARCHITECTURE.md` if component responsibilities, data flow, storage schema, or runtime flow change.
- Update `docs/ROADMAP.md` if planned work, priorities, or known future directions change.
- Update `docs/LAST_CHANGES.md` with the newest concise summary.
- Append a dated entry to `docs/CHANGELOGS.md` for every completed change, including documentation-only changes.

Keep changelog entries newest first. Mention files or areas touched, why they changed, and any verification done.

## Optional Codebase Index

If the `codebase-index` tool is available and the local index is fresh, use it before broad manual scans for architecture, symbol, reference, impact, or data-flow questions:

```sh
codebase-index explain "architecture overview" --token-budget 3000 --json
codebase-index search "query" --json
codebase-index symbol "SymbolName" --json
codebase-index refs "SymbolName" --json
codebase-index impact "path/or/symbol" --json
```

If the index is missing, run `codebase-index index`. If it is stale, run `codebase-index update` for small changes or `codebase-index index` for a full rebuild. Always verify important conclusions in the source files before editing.

## Project Map

- `cinedive/app/main.py` selects polling or webhook mode, installs routers, injects database sessions through middleware, and serves `/health` in webhook mode.
- `cinedive/app/config.py` owns pydantic-settings configuration and required-secret checks.
- `cinedive/app/bot/handlers/` contains Telegram UX only. Do not put database queries or recommendation algorithms directly in handlers.
- `cinedive/app/bot/keyboards/` contains reply and inline keyboard builders.
- `cinedive/app/bot/states/` contains aiogram FSM state groups.
- `cinedive/app/bot/middlewares/` contains aiogram middleware such as async database session injection.
- `cinedive/app/database/models/` contains SQLAlchemy ORM models only.
- `cinedive/app/database/repositories/` contains database access and persistence operations.
- `cinedive/app/services/` contains business logic and external API integration.
- `alembic/` contains database migration configuration and revisions.
- `deploy/postgres/init/` contains PostgreSQL bootstrap scripts used by Docker Compose deployments.
- `.github/workflows/deploy.yml` publishes the Docker image to GHCR and restarts the remote Docker Compose deployment.
- `docs/` contains persistent project context for agents.

## Coding Guidelines

- Use Python 3.11+ and aiogram 3 patterns.
- Prefer small, direct changes that preserve the current layer boundaries.
- Keep Telegram handlers focused on user interaction, state transitions, and response rendering.
- Use webhook mode for production. Polling is only an optional local development mode behind `BOT_MODE=polling`.
- Callback query handlers must call `await callback.answer()` before TMDB calls, database work, or other slow operations.
- Keep TMDB API calls inside `TMDBService`; do not call HTTP clients directly from handlers.
- Keep SQLAlchemy queries inside repositories; services should depend on repositories instead of raw sessions when business logic grows.
- Do not implement the party/match system until explicitly requested. Keep schemas and services extensible, but avoid speculative code.
- Do not implement ML recommendations in the MVP. Use simple score-based ranking when recommendations are added.
- Do not download, upload, proxy, or send soundtrack/music files. Soundtrack behavior should return external links to legal music platforms only.
- Soundtrack integrations may use official/public APIs to resolve platform links. If a confident match cannot be resolved, fall back to platform search links.
- Do not use unofficial downloaders, ripping tools, scraping that violates platform terms, or Telegram audio delivery for copyrighted music. Cache only metadata and external URLs, never audio files.
- Do not commit secrets or `.env`; use `.env.example` for documented variables.
- Escape dynamic user-provided text before inserting it into HTML Telegram messages.

## Current Scope Guardrails

- `/start` registers or updates the Telegram user, asks new users for favorite genres, saves selected genres, and shows the main menu.
- `BOT_MODE=webhook` starts an aiohttp web server, registers the Telegram webhook with `secret_token`, and exposes `GET /health`.
- `BOT_MODE=polling` is local-development only and deletes any existing webhook before polling.
- Main menu buttons exist for Recommend, Wishlist, Search, and Profile.
- Search is wired to TMDB and persists selected media cards. Wishlist, watched, rating, mood, recommendation, and soundtrack platform-link flows are implemented.
- SQLAlchemy models and the initial Alembic migration define the planned persistence model.
- TMDB integration exists as a reusable async client and is wired into the search UI.
- GitHub Actions deployment publishes the Docker image to GHCR, runs Alembic migrations on the remote host, and restarts Docker Compose.

## Local Verification Policy

Reasonable local verification for this Python project:

- Run syntax compilation with `python -m compileall cinedive alembic` when Python is available.
- Run `ruff check .` if dev dependencies are installed.
- Run Alembic migrations against a local PostgreSQL instance only when `.env` is configured and PostgreSQL is running.
- Do not install dependencies, start Docker services, or modify system package manager state unless the user explicitly asks.

Runtime requires at least `BOT_TOKEN`, `DATABASE_URL`, and `TMDB_API_KEY` once TMDB-backed flows are active.
