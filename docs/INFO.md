# Info

`cinedive-tg-bot` is a Python Telegram bot for movie and TV show recommendations. Users will be able to search TMDB media, save wishlist items, mark media as watched, rate items, and receive simple mood-aware recommendations.

## Current State

- Clean MVP skeleton is in place.
- aiogram 3 entry point is available at `python -m cinedive.app.main`.
- Production webhook mode is supported through aiohttp and Telegram `secret_token` validation.
- Optional local polling mode is available with `BOT_MODE=polling`.
- `/start` registers or updates Telegram users in PostgreSQL.
- New users can choose favorite genres from an inline onboarding keyboard.
- Main menu buttons exist for Recommend, Wishlist, Search, and Profile.
- Profile displays stored favorite genres.
- Search is wired to TMDB multi-search for movies and TV shows.
- Selecting a search result fetches TMDB details, persists the media item, localized translation, and genre links, then renders a media card with poster and action buttons.
- Users can add media cards to a wishlist, list wishlist items, reopen saved cards, and remove items.
- Users can mark media as watched and save a 1-10 rating with `rated_at`.
- Users can choose a temporary 24-hour mood preset and receive simple non-ML recommendations from saved TMDB media, excluding watched and temporarily hidden items.
- Telegram-facing UI texts and labels are loaded from English/Russian YAML locale files based on the user's Telegram locale, with English fallback.
- SQLAlchemy models and Alembic initial migration define the planned database schema.
- TMDB async client exists with search, movie details, TV details, and genre methods.
- GitHub Actions deployment is configured to publish a GHCR image, copy Docker Compose deployment files to a remote host, run Alembic migrations, and restart the webhook service.

## MVP Direction

- Add soundtrack links to legal external music platforms, resolving direct platform links when official/public APIs make that practical and falling back to platform search links when needed.

## Explicitly Out Of Scope For Now

- Party/match system.
- ML recommendations.
- Downloading, proxying, uploading, or sending music files.
- Deployment hardening beyond the current GHCR, Docker Compose, and aiohttp webhook path.
