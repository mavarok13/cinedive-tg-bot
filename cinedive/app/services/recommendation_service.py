from dataclasses import dataclass
from math import ceil
from random import Random

from cinedive.app.database.repositories.media_repository import RecommendationCandidate
from cinedive.app.database.repositories.recommendation_repository import DiscoveryStrategyDraft, RecommendationQueueDraft


MOVIE_DISCOVER_GENRES = {
    12,
    14,
    16,
    18,
    27,
    28,
    35,
    36,
    37,
    53,
    80,
    99,
    878,
    9648,
    10402,
    10749,
    10751,
    10752,
}
TV_DISCOVER_GENRES = {
    16,
    18,
    35,
    37,
    80,
    99,
    9648,
    10751,
    10759,
    10762,
    10763,
    10764,
    10765,
    10766,
    10767,
    10768,
}
DISCOVERY_LANGUAGE_ROTATION = ("en", "ko", "ja", "fr", "es")
DISCOVERY_COUNTRY_ROTATION = ("US", "KR", "JP", "GB", "FR")


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


@dataclass(frozen=True)
class DiscoveryStrategy:
    media_type: str
    sort_by: str
    genre_key: str
    genre_ids: set[int]
    filter_key: str
    vote_count_gte: int
    vote_average_gte: float
    original_language: str | None = None
    origin_country: str | None = None

    @property
    def draft(self) -> DiscoveryStrategyDraft:
        return DiscoveryStrategyDraft(
            media_type=self.media_type,
            sort_by=self.sort_by,
            genre_key=self.genre_key,
            filter_key=self.filter_key,
        )


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

    def build_discovery_strategies(
        self,
        *,
        content_type: str,
        favorite_genre_ids: set[int],
        mood_genre_ids: set[int],
    ) -> list[DiscoveryStrategy]:
        strategies_by_media_type: list[list[DiscoveryStrategy]] = []
        for media_type in _discover_media_types(content_type):
            media_type_strategies: list[DiscoveryStrategy] = []
            genre_variants = _genre_variants(
                media_type=media_type,
                favorite_genre_ids=favorite_genre_ids,
                mood_genre_ids=mood_genre_ids,
            )
            date_sort = "primary_release_date.desc" if media_type == "movie" else "first_air_date.desc"
            sort_filters = (
                ("popularity.desc", "quality", 100, 6.0),
                ("vote_count.desc", "trusted", 150, 6.0),
                ("vote_average.desc", "high_votes", 500, 6.3),
                (date_sort, "recent", 30, 5.5),
            )
            for genre_key, genre_ids in genre_variants:
                for sort_by, filter_key, vote_count_gte, vote_average_gte in sort_filters:
                    media_type_strategies.append(
                        DiscoveryStrategy(
                            media_type=media_type,
                            sort_by=sort_by,
                            genre_key=genre_key,
                            genre_ids=genre_ids,
                            filter_key=filter_key,
                            vote_count_gte=vote_count_gte,
                            vote_average_gte=vote_average_gte,
                        )
                    )
            for language in DISCOVERY_LANGUAGE_ROTATION:
                media_type_strategies.append(
                    DiscoveryStrategy(
                        media_type=media_type,
                        sort_by="popularity.desc",
                        genre_key="broad",
                        genre_ids=set(),
                        filter_key=f"lang:{language}",
                        vote_count_gte=80,
                        vote_average_gte=5.8,
                        original_language=language,
                    )
                )
            for country in DISCOVERY_COUNTRY_ROTATION:
                media_type_strategies.append(
                    DiscoveryStrategy(
                        media_type=media_type,
                        sort_by="vote_count.desc",
                        genre_key="broad",
                        genre_ids=set(),
                        filter_key=f"country:{country}",
                        vote_count_gte=80,
                        vote_average_gte=5.8,
                        origin_country=country,
                    )
                )
            strategies_by_media_type.append(media_type_strategies)

        strategies: list[DiscoveryStrategy] = []
        max_strategy_count = max((len(items) for items in strategies_by_media_type), default=0)
        for index in range(max_strategy_count):
            for media_type_strategies in strategies_by_media_type:
                if index < len(media_type_strategies):
                    strategies.append(media_type_strategies[index])
        return strategies

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


def _discover_media_types(content_type: str) -> tuple[str, ...]:
    if content_type in {"movie", "tv"}:
        return (content_type,)
    return ("movie", "tv")


def _genre_variants(
    *,
    media_type: str,
    favorite_genre_ids: set[int],
    mood_genre_ids: set[int],
) -> list[tuple[str, set[int]]]:
    variants: list[tuple[str, set[int]]] = []
    valid_genres = MOVIE_DISCOVER_GENRES if media_type == "movie" else TV_DISCOVER_GENRES
    for key, genre_ids in (
        ("mood", mood_genre_ids),
        ("favorite", favorite_genre_ids),
        ("mixed", favorite_genre_ids | mood_genre_ids),
    ):
        filtered = genre_ids & valid_genres
        if filtered:
            variants.append((f"{key}:{_genre_key(filtered)}", filtered))
    variants.append(("broad", set()))
    return list(dict(variants).items())


def _genre_key(genre_ids: set[int]) -> str:
    return ",".join(str(genre_id) for genre_id in sorted(genre_ids))
