from dataclasses import dataclass

from cinedive.app.database.repositories.media_repository import RecommendationCandidate


@dataclass(frozen=True)
class RecommendationScore:
    genre_match: float
    tmdb_rating: float
    popularity: float
    collaborative: float = 0.0

    @property
    def total(self) -> float:
        return self.genre_match * 3 + self.tmdb_rating * 1.5 + self.popularity + self.collaborative


class RecommendationService:
    def recommend(
        self,
        candidates: list[RecommendationCandidate],
        *,
        favorite_genre_ids: set[int],
        mood_genre_ids: set[int],
        collaborative_scores: dict[int, float] | None = None,
        limit: int = 5,
    ) -> list[RecommendationCandidate]:
        weighted: list[tuple[float, RecommendationCandidate]] = []
        for candidate in candidates:
            score = self.score(
                candidate,
                favorite_genre_ids=favorite_genre_ids,
                mood_genre_ids=mood_genre_ids,
                collaborative_scores=collaborative_scores or {},
            )
            weighted.append((score.total, candidate))
        weighted.sort(key=lambda item: item[0], reverse=True)
        return [candidate for _, candidate in weighted[:limit]]

    def score(
        self,
        candidate: RecommendationCandidate,
        *,
        favorite_genre_ids: set[int],
        mood_genre_ids: set[int],
        collaborative_scores: dict[int, float],
    ) -> RecommendationScore:
        preferred_genres = favorite_genre_ids | mood_genre_ids
        genre_match = 0.0
        if preferred_genres and candidate.genre_external_ids:
            genre_match = len(candidate.genre_external_ids & preferred_genres) / len(preferred_genres)
        tmdb_rating = (candidate.card.tmdb_rating or 0.0) / 10
        popularity = min((candidate.card.tmdb_vote_count or 0) / 1000, 1.0)
        return RecommendationScore(
            genre_match=genre_match,
            tmdb_rating=tmdb_rating,
            popularity=popularity,
            collaborative=collaborative_scores.get(candidate.card.id, 0.0),
        )
