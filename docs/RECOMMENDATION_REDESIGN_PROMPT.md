# Recommendation Redesign Prompt

Use this prompt when asking an AI coding agent to implement the next recommendation-system iteration.

```text
Implement the CineDive recommendation feed redesign.

Context:
- This is a Python 3.11+ aiogram 3 Telegram bot with SQLAlchemy async ORM, Alembic, PostgreSQL, and TMDB integration.
- Keep Telegram handlers focused on UX. Put scoring and batch logic in services, database access in repositories, and TMDB HTTP calls only in TMDBService.
- Keep the recommendation system non-ML. Do not add external recommendation APIs or scraping.
- Read AGENTS.md and docs/*.md before editing, then update docs/LAST_CHANGES.md and docs/CHANGELOGS.md after the change.

Goal:
Replace the current deterministic “return the single top-scored candidate” recommendation flow with a mood-session-bound batch queue. The feed should be diverse, avoid repetition, learn from Hide/Wishlist/Rating signals, and avoid low-quality media cards.

Database changes:
1. Extend the user-media state model, preferably by evolving the existing user_media table rather than renaming it unless a rename is clearly worth the migration risk.
2. Track long-lived user/media memory with fields such as last_shown_at, shown_count, wishlist_at, watched_at, ignored_at, hidden_until, last_interaction_at, rating, and rated_at. Avoid a single status field becoming the only source of truth if it prevents a media item from being both shown and wishlisted/rated.
3. Add recommendation_queue_items with at least user_id, mood_session_id, media_id, position, bucket, score, shown_at, created_at, and expires_at.
4. Add user_preference_penalties with at least user_id, feature_type, feature_value, weight, created_at, updated_at, and an expiry or decay mechanism. Feature types should support genre, origin_country, original_language, and optionally media_type/company.
5. Add media metadata needed for diversity and penalties where practical, especially origin_country or production countries from TMDB. original_language already exists and can be used as a weaker fallback.

Mood-session behavior:
1. When a user opens a new mood session, close or delete the previous active mood session for that user and clear its queue.
2. The queue belongs to the active mood session. If the mood session expires, delete or ignore the queue.
3. If the queue is exhausted while the mood session is still active, generate a fresh queue for the same mood session.
4. Keep shown history in user_media so old queue deletion does not allow immediate repetition.

Candidate sourcing and filtering:
1. Source candidates from TMDB Discover and persisted media, using favorite genres, mood genres, content type, runtime, rating, vote count, popularity, and release-date filters.
2. Do not rely only on the first TMDB Discover page sorted by vote_average.desc. Use multiple pages or varied sort/filter strategies to avoid a narrow feed.
3. Exclude candidates that have no poster or no usable localized/fallback overview whenever practical.
4. Exclude watched, rated, ignored, currently hidden, and recently shown media.
5. Apply a cooldown for last_shown_at, for example 30 days initially.

Scoring:
Calculate a personal_score from content relevance and collaborative signals, for example:
- favorite genre match
- mood genre match
- normalized TMDB rating, weighted by vote-count confidence
- popularity or vote-count confidence
- ratings from similar users
- wishlist signals from similar users
- user preference penalties
- repetition penalty

Batch composition:
1. Generate a batch of around 20-50 items.
2. Split candidates into buckets by personal_score and exploration value.
3. Fill the queue roughly as: large high-confidence share, smaller medium-confidence share, and small exploration share. A reasonable starting point is 60% high-confidence, 30% medium-confidence, 10% exploration.
4. Pick items within buckets using weighted randomness rather than deterministic top-N only.
5. Shuffle the final queue while preserving bucket proportions.
6. Enforce diversity caps so no single origin country, original language, genre cluster, or media type dominates the batch. This is especially important for TV content such as Korean dramas with high TMDB ratings.

User feedback behavior:
1. Next should mark the current media as shown and usually be neutral or only a very weak negative signal.
2. Hide should hide the exact media item and add decaying penalties for related features: genre, origin country, original language, and optionally media type/company.
3. Wishlist should be a positive signal for similar future recommendations.
4. Ratings should be strong feedback: high ratings boost similar content, low ratings penalize similar content.
5. Preference penalties should accumulate but gradually recover over time. Do not permanently ban a genre or country from a single hide.

Verification:
- Add or update tests where the project already has a test pattern; otherwise keep changes small and manually verifiable.
- Run python -m compileall cinedive alembic.
- Run ruff check . if Ruff is installed.
- Do not run Alembic against a real database unless a local DATABASE_URL/PostgreSQL setup is explicitly available.
```
