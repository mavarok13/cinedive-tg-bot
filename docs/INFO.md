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
- Telegram-facing UI texts and labels are loaded from English/Russian YAML locale files based on the user's Telegram locale, with English fallback.
- SQLAlchemy models and Alembic initial migration define the planned database schema.
- TMDB async client exists with search, movie details, TV details, and genre methods.

## MVP Direction

- Wire Search to TMDB and persist selected media cards.
- Add wishlist add/remove and media-card rendering.
- Add watched and 1-10 rating flow.
- Add simple non-ML recommendations based on favorite genres, TMDB rating, and popularity.
- Add temporary 48-hour mood sessions separate from long-term genre preferences.
- Add soundtrack external search links only.

## Explicitly Out Of Scope For Now

- Party/match system.
- ML recommendations.
- Downloading or sending music files.
- Webhook deployment hardening beyond the basic aiohttp server.
