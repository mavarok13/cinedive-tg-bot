# Architecture

`cinedive-tg-bot` is organized as a layered aiogram application. Telegram handlers handle UX, services contain business logic and external integrations, repositories own database access, and models define persistence.

## Current Startup Flow

1. `cinedive/app/main.py` loads settings from `cinedive/app/config.py`.
2. aiogram `Bot` is created with HTML parse mode.
3. `Dispatcher` is created and receives `DbSessionMiddleware`.
4. Routers from `cinedive/app/bot/handlers/` are registered.
5. If `BOT_MODE=polling`, existing webhook state is dropped and long polling starts. This mode is for local development only.
6. If `BOT_MODE=webhook`, an aiohttp app is created, `GET /health` is registered, the Telegram webhook route is registered with `SimpleRequestHandler`, and `bot.set_webhook` is called on startup with Telegram `secret_token`.
7. Webhook mode starts `TCPSite` on `WEB_SERVER_HOST:WEB_SERVER_PORT` and does not call `Dispatcher.start_polling()`.
8. On shutdown, the bot HTTP session and SQLAlchemy async engine are closed.

## Layer Boundaries

### Bot Layer

Files: `cinedive/app/bot/`

- `handlers/` contains Telegram messages, callbacks, FSM transitions, and responses.
- `keyboards/` builds reply and inline keyboards.
- `states/` defines aiogram FSM state groups.
- `middlewares/` injects infrastructure such as async database sessions.
- `cinedive/app/localization.py` loads packaged YAML UI strings from `cinedive/lang/` and selects English or Russian from Telegram `language_code`, falling back to English.

Handlers should not contain SQLAlchemy query construction, TMDB HTTP calls, or recommendation scoring. Callback query handlers must acknowledge with `await callback.answer()` before database work, TMDB calls, message edits, or other slow operations.

### Service Layer

Files: `cinedive/app/services/`

- `TMDBService` wraps TMDB HTTP requests.
- `RecommendationService` is reserved for simple non-ML recommendation ranking.
- `MoodService` owns mood-session expiration rules.
- `SoundtrackService` builds external soundtrack links to legal music platforms for the MVP.

Services should contain business decisions and use repositories for persistence as flows grow.

### Database Layer

Files: `cinedive/app/database/`

- `base.py` defines SQLAlchemy declarative base and timestamp mixin.
- `session.py` creates the async engine and session factory.
- `models/` defines ORM mappings.
- `repositories/` provides persistence operations.

Database code should not import aiogram types or Telegram-specific objects.

## Persistence Model

The initial schema contains:

- `users`: Telegram users.
- `genres`: TMDB genres by source, external ID, and media type.
- `user_genres`: user favorite genres with weights.
- `media_items`: normalized TMDB movie and TV records.
- `media_translations`: localized titles and overviews.
- `media_genres`: media-to-genre links.
- `user_media`: wishlist, watched, hidden, ignored statuses and optional 1-10 rating.
- `user_mood_sessions`: temporary mood preferences with expiry.
- `soundtracks`: future cache for external soundtrack platform metadata and links.

The `media_items` table has a unique constraint on `(source, external_id, media_type)`. `user_media` uses `(user_id, media_id)` as the primary key.

## Implemented User Flow

1. User sends `/start`.
2. `start.py` creates or updates the user through `UserRepository`.
3. Handlers render localized copy and keyboard labels from `cinedive/lang/*.yml` using the user's Telegram locale.
4. If favorite genres already exist, the main menu is shown.
5. Otherwise, an inline genre keyboard is shown.
6. `onboarding.py` toggles genre rows and user-genre links through repositories.
7. When the user presses Done, the main menu is shown.
8. User presses Search and `search.py` asks for a query through `SearchStates`.
9. Search delegates TMDB lookup and detail fetches to `TMDBService`.
10. Selected results are persisted through `MediaRepository` and `GenreRepository` as media items, translations, and media-genre links.
11. The handler renders a localized media card with poster, metadata, overview, and existing action callbacks.
12. Wishlist callbacks store or remove `user_media` rows with `wishlist` status and can reopen persisted media cards.
13. Watched and rating callbacks use `RatingStates` to ask for a 1-10 rating and persist `watched`, `rating`, and `rated_at` through `UserMediaRepository`.
14. Recommend checks for an active 24-hour mood session, asks for a mood preset when needed, and renders a scored recommendation from persisted media.
15. Next/Hide callbacks temporarily hide media for the mood window so recommendation candidates rotate.

## MVP Data Flow

Search flow:

1. Handler asks for query and delegates to `TMDBService.search_media`.
2. User chooses a result from inline buttons backed by FSM state.
3. Details and canonical TMDB genre names are fetched through `TMDBService`.
4. Media item, localized translation, and genre links are persisted through repositories.
5. Handler renders a media card with poster and action callbacks.

Wishlist and rating flow:

1. Media-card callbacks save wishlist status or start the rating flow.
2. The Wishlist menu lists saved cards from persisted media data and lets users reopen or remove items.
3. Watched/rate callbacks ask for a 1-10 rating using FSM state and inline rating buttons.
4. `UserMediaRepository` persists wishlist/watched status, rating, and `rated_at`.

Recommendation flow:

1. Handler checks active mood session through mood repository/service.
2. If needed, handler asks a temporary mood preset question and stores the selected mood separately from favorite genres.
3. Handler seeds candidates from TMDB Discover using favorite genres, mood genres, content type, rating, vote count, runtime, and release-date filters.
4. Discovered candidates are fetched through `TMDBService`, persisted as normal media items/translations/genre links, and then loaded from `MediaRepository`.
5. `MediaRepository` excludes watched, ignored, hidden, and already-rated media.
6. `RecommendationService` ranks candidates with a simple non-ML score from favorite genre match, mood genre match, TMDB rating, vote count, and collaborative rating boost when similar-user ratings exist.
7. Handler renders the next media card.

Soundtrack flow:

1. Handler resolves the current media title.
2. `SoundtrackService` queries Deezer public API for a confident direct soundtrack match.
3. If a direct match is unavailable, `SoundtrackService` falls back to legal platform search links for Deezer, YouTube Music, Spotify, Apple Music, and Yandex Music.
4. `SoundtrackRepository` caches only metadata and external URLs in `soundtracks`.
5. No music files are downloaded, proxied, uploaded, cached, or sent through Telegram.

## Deployment Flow

1. `.github/workflows/deploy.yml` runs on pushes to `main` or manual dispatch.
2. The workflow builds the Docker image from `Dockerfile` and publishes `latest` plus commit-SHA tags to GHCR.
3. The workflow copies `docker-compose.yml` and `deploy/postgres/init/01-create-app-database.sh` to `/home/deploy/apps/cinedive-tg-bot` on the remote host.
4. The SSH restart step updates remote deployment variables, starts PostgreSQL, runs `alembic upgrade head` through the bot image, and restarts Docker Compose.
5. `docker-compose.yml` runs PostgreSQL with a bootstrap superuser and the bot with a non-superuser app role over `postgresql+asyncpg`.

## Important Constraints

- Keep the party/match system out of the MVP implementation until explicitly requested.
- Keep recommendation ranking non-ML for the MVP.
- Do not mix Telegram UX, business rules, and SQLAlchemy queries in one file.
- Production uses webhook mode. Polling is local-only behind `BOT_MODE=polling`.
- PostgreSQL JSONB is used for mood tags, so the primary database target is PostgreSQL.
