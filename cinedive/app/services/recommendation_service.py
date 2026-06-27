from dataclasses import dataclass


@dataclass(frozen=True)
class RecommendationScore:
    genre_match: float
    tmdb_rating: float
    popularity: float

    @property
    def total(self) -> float:
        return self.genre_match * 3 + self.tmdb_rating * 1.5 + self.popularity


class RecommendationService:
    """Simple non-ML recommendation service placeholder for the next MVP stage."""

    async def recommend_for_user(self, user_id: int, limit: int = 5) -> list[object]:
        _ = (user_id, limit)
        return []
