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
- `SoundtrackService` builds external soundtrack search links for the MVP.

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
- `soundtracks`: future cache for external soundtrack links.

The `media_items` table has a unique constraint on `(source, external_id, media_type)`. `user_media` uses `(user_id, media_id)` as the primary key.

## Implemented User Flow

1. User sends `/start`.
2. `start.py` creates or updates the user through `UserRepository`.
3. Handlers render localized copy and keyboard labels from `cinedive/lang/*.yml` using the user's Telegram locale.
4. If favorite genres already exist, the main menu is shown.
5. Otherwise, an inline genre keyboard is shown.
6. `onboarding.py` toggles genre rows and user-genre links through repositories.
7. When the user presses Done, the main menu is shown.

## Planned MVP Data Flow

Search flow:

1. Handler asks for query and delegates to `TMDBService.search_media`.
2. User chooses a result.
3. Details are fetched from TMDB and persisted through `MediaRepository`.
4. Handler renders a media card with action callbacks.

Recommendation flow:

1. Handler checks active mood session through mood repository/service.
2. If needed, handler asks temporary mood questions.
3. `RecommendationService` loads favorite genres, excludes watched/hidden media, and ranks candidates with a simple score.
4. Handler renders the next media card.

Soundtrack flow:

1. Handler resolves the current media title.
2. `SoundtrackService` returns an external YouTube search URL.
3. No music files are downloaded or sent.

## Important Constraints

- Keep the party/match system out of the MVP implementation until explicitly requested.
- Keep recommendation ranking non-ML for the MVP.
- Do not mix Telegram UX, business rules, and SQLAlchemy queries in one file.
- Production uses webhook mode. Polling is local-only behind `BOT_MODE=polling`.
- PostgreSQL JSONB is used for mood tags, so the primary database target is PostgreSQL.
