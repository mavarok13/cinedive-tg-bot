from dataclasses import dataclass
from math import ceil
from random import Random

from cinedive.app.database.repositories.media_repository import RecommendationCandidate
from cinedive.app.database.repositories.recommendation_repository import RecommendationQueueDraft


@dataclass(frozen=True)
class RecommendationScore:
    favorite_genre: float
    mood_genre: float
    tmdb_quality: float
    popularity: float
    collaborative_rating: float = 0.0
    collaborative_wishlist: float = 0.0
    preference_penalty: float = 0.0
    repetition_penalty: float = 0.0

    @property
    def total(self) -> float:
        return max(
            self.favorite_genre * 2.0
            + self.mood_genre * 1.6
            + self.tmdb_quality * 1.5
            + self.popularity * 0.7
            + self.collaborative_rating
            + self.collaborative_wishlist * 0.8
            - self.preference_penalty
            - self.repetition_penalty,
            0.01,
        )


@dataclass(frozen=True)
class _ScoredCandidate:
    candidate: RecommendationCandidate
    score: float


class RecommendationService:
    def __init__(self, randomizer: Random | None = None) -> None:
        self._random = randomizer or Random()

    def build_queue(
        self,
        candidates: list[RecommendationCandidate],
        *,
        favorite_genre_ids: set[int],
        mood_genre_ids: set[int],
        collaborative_scores: dict[int, float] | None = None,
        wishlist_scores: dict[int, float] | None = None,
        preference_penalties: dict[tuple[str, str], float] | None = None,
        batch_size: int = 30,
    ) -> list[RecommendationQueueDraft]:
        scored = [
            _ScoredCandidate(
                candidate=candidate,
                score=self.score(
                    candidate,
                    favorite_genre_ids=favorite_genre_ids,
                    mood_genre_ids=mood_genre_ids,
                    collaborative_scores=collaborative_scores or {},
                    wishlist_scores=wishlist_scores or {},
                    preference_penalties=preference_penalties or {},
                ).total,
            )
            for candidate in candidates
        ]
        if not scored:
            return []

        scored.sort(key=lambda item: item.score, reverse=True)
        high_pool = scored[: max(1, ceil(len(scored) * 0.4))]
        medium_pool = scored[max(1, ceil(len(scored) * 0.3)) : max(1, ceil(len(scored) * 0.8))]
        exploration_pool = [item for item in scored if item not in high_pool]

        target_size = min(batch_size, len(scored))
        targets = {
            "high": ceil(target_size * 0.6),
            "medium": ceil(target_size * 0.3),
            "exploration": target_size,
        }
        targets["exploration"] = max(target_size - targets["high"] - targets["medium"], 0)

        selected: list[tuple[str, _ScoredCandidate]] = []
        used_media_ids: set[int] = set()
        for bucket, pool in (
            ("high", high_pool),
            ("medium", medium_pool),
            ("exploration", exploration_pool),
        ):
            selected.extend(
                self._weighted_pick(
                    pool,
                    bucket=bucket,
                    count=targets[bucket],
                    selected=selected,
                    used_media_ids=used_media_ids,
                    target_size=target_size,
                )
            )

        if len(selected) < target_size:
            selected.extend(
                self._weighted_pick(
                    scored,
                    bucket="medium",
                    count=target_size - len(selected),
                    selected=selected,
                    used_media_ids=used_media_ids,
                    target_size=target_size,
                    relax_diversity=True,
                )
            )

        self._random.shuffle(selected)
        return [
            RecommendationQueueDraft(
                media_id=item.candidate.card.id,
                bucket=bucket,
                score=item.score,
            )
            for bucket, item in selected[:target_size]
        ]

    def score(
        self,
        candidate: RecommendationCandidate,
        *,
        favorite_genre_ids: set[int],
        mood_genre_ids: set[int],
        collaborative_scores: dict[int, float],
        wishlist_scores: dict[int, float],
        preference_penalties: dict[tuple[str, str], float],
    ) -> RecommendationScore:
        favorite_genre = _overlap_ratio(candidate.genre_external_ids, favorite_genre_ids)
        mood_genre = _overlap_ratio(candidate.genre_external_ids, mood_genre_ids)
        vote_confidence = min((candidate.card.tmdb_vote_count or 0) / 800, 1.0)
        tmdb_quality = ((candidate.card.tmdb_rating or 0.0) / 10) * (0.5 + vote_confidence / 2)
        popularity = min((candidate.card.tmdb_vote_count or 0) / 1500, 1.0)
        return RecommendationScore(
            favorite_genre=favorite_genre,
            mood_genre=mood_genre,
            tmdb_quality=tmdb_quality,
            popularity=popularity,
            collaborative_rating=collaborative_scores.get(candidate.card.id, 0.0),
            collaborative_wishlist=wishlist_scores.get(candidate.card.id, 0.0),
            preference_penalty=_preference_penalty(candidate, preference_penalties),
            repetition_penalty=min(candidate.shown_count * 0.25, 1.0),
        )

    def _weighted_pick(
        self,
        pool: list[_ScoredCandidate],
        *,
        bucket: str,
        count: int,
        selected: list[tuple[str, _ScoredCandidate]],
        used_media_ids: set[int],
        target_size: int,
        relax_diversity: bool = False,
    ) -> list[tuple[str, _ScoredCandidate]]:
        picked: list[tuple[str, _ScoredCandidate]] = []
        candidates = [item for item in pool if item.candidate.card.id not in used_media_ids]
        while candidates and len(picked) < count:
            item = self._weighted_choice(candidates)
            candidates.remove(item)
            if not relax_diversity and not _fits_diversity(selected + picked, item, target_size):
                continue
            used_media_ids.add(item.candidate.card.id)
            picked.append((bucket, item))
        return picked

    def _weighted_choice(self, candidates: list[_ScoredCandidate]) -> _ScoredCandidate:
        total_weight = sum(item.score for item in candidates)
        if total_weight <= 0:
            return self._random.choice(candidates)
        threshold = self._random.uniform(0, total_weight)
        current = 0.0
        for item in candidates:
            current += item.score
            if current >= threshold:
                return item
        return candidates[-1]


def _overlap_ratio(candidate_genres: set[int], preferred_genres: set[int]) -> float:
    if not candidate_genres or not preferred_genres:
        return 0.0
    return len(candidate_genres & preferred_genres) / len(preferred_genres)


def _preference_penalty(
    candidate: RecommendationCandidate,
    penalties: dict[tuple[str, str], float],
) -> float:
    total = penalties.get(("media_type", candidate.card.media_type), 0.0) * 0.25
    if candidate.original_language:
        total += penalties.get(("original_language", candidate.original_language), 0.0) * 0.35
    if candidate.origin_country:
        total += penalties.get(("origin_country", candidate.origin_country), 0.0) * 0.45
    for genre_id in candidate.genre_external_ids:
        total += penalties.get(("genre", str(genre_id)), 0.0) * 0.25
    return min(total, 2.0)


def _fits_diversity(
    selected: list[tuple[str, _ScoredCandidate]],
    item: _ScoredCandidate,
    target_size: int,
) -> bool:
    language_cap = max(2, ceil(target_size * 0.35))
    country_cap = max(2, ceil(target_size * 0.35))
    media_type_cap = max(3, ceil(target_size * 0.7))
    return (
        _feature_count(selected, "original_language", item.candidate.original_language) < language_cap
        and _feature_count(selected, "origin_country", item.candidate.origin_country) < country_cap
        and _feature_count(selected, "media_type", item.candidate.card.media_type) < media_type_cap
    )


def _feature_count(
    selected: list[tuple[str, _ScoredCandidate]],
    feature: str,
    value: str | None,
) -> int:
    if value is None:
        return 0
    count = 0
    for _, item in selected:
        if feature == "media_type" and item.candidate.card.media_type == value:
            count += 1
        elif feature == "origin_country" and item.candidate.origin_country == value:
            count += 1
        elif feature == "original_language" and item.candidate.original_language == value:
            count += 1
    return count
