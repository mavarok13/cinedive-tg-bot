# Roadmap

## Stage 1: Skeleton And Basic Start Flow

Status: complete.

- Create Python project layout.
- Configure dependencies and environment settings.
- Configure async PostgreSQL connection.
- Define SQLAlchemy models and Alembic migration.
- Add basic repositories.
- Add empty or placeholder handlers/keyboards/states for planned MVP flows.
- Implement `/start`, user registration, genre onboarding, and main menu.
- Add a basic TMDB client.
- Add production webhook mode with aiohttp, Telegram `secret_token`, and `GET /health`.
- Add GitHub Actions deployment through GHCR, Docker Compose, and Alembic migrations.
- Add persistent AI guidance docs.

## Stage 2: TMDB Search And Media Cards

Status: complete.

- Wire Search FSM to `TMDBService.search_media`.
- Render result choices.
- Fetch movie or TV details after selection.
- Persist media item, translation, and genre links.
- Render media card with poster and buttons.

## Stage 3: Wishlist, Watched, And Rating

Status: complete.

- Add wishlist add/list/open/remove flows.
- Add watched callback.
- Ask for rating from 1 to 10 after watched.
- Save rating and `rated_at`.

## Stage 4: Recommendations And Mood Sessions

Status: complete.

- Add mood session questions when no active session exists or it is older than 24 hours.
- Store temporary mood preferences separately from favorite genres.
- Implement simple recommendation scoring from genre match, TMDB rating, and popularity.
- Exclude watched and temporarily hidden media.

## Stage 4.5: Hybrid Recommendation Expansion

Status: complete.

- Add TMDB Discover candidate sourcing so recommendations are not limited to media already searched by users.
- Seed candidates from favorite genres, mood genres, content type, TMDB rating, vote count, popularity, runtime, and release-year filters.
- Persist discovered candidates as normal `media_items`, translations, and media-genre links before ranking.
- Keep content-based ranking as the default fallback for cold-start users and low-rating datasets.
- Add collaborative boost from users with similar favorite genres and rating history once enough user ratings exist.
- Exclude the current user's watched, ignored, hidden, and already-rated media from recommendation results.
- Keep IMDb as an external identifier only for now; do not depend on IMDb scraping or unofficial APIs for recommendations.

## Stage 5: Soundtrack Platform Links

- Return external links to legal music platforms for soundtrack requests.
- Resolve direct platform links through official/public APIs where practical, with platform search links as fallback.
- Optionally cache platform metadata and external links in `soundtracks`.
- Do not download, proxy, upload, or send music files.

## Later: Party/Match System

- Design multi-user session model.
- Let users vote/swipe through candidate media.
- Find common matches.
- Keep this out of MVP until the base bot is stable.
