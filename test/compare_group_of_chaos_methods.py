"""Compare Group of Chaos scoring methods against predictions.json + MC pair data."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

from src.config import RANDOM_SEED, WC2026_GROUPS
from src.helpers import get_group_fixtures
from src.models import load_models
from src.preprocessing import load_and_preprocess
from src.simulations import (
    build_feature_cache,
    build_lambda_cache,
    _draw_group_stage_batch,
    _group_standings_from_batch,
)

PREDICTIONS_PATH = Path("output/predictions.json")


def _variance_score(probs: list[float]) -> float:
    if len(probs) < 2:
        return 0.0
    mean = sum(probs) / len(probs)
    return sum((prob - mean) ** 2 for prob in probs) / len(probs)


def _shannon_entropy(probs: list[float]) -> float:
    total = sum(probs)
    if total <= 0:
        return 0.0
    normalized = [prob / total for prob in probs if prob > 0]
    return -sum(prob * math.log(prob) for prob in normalized)


def _favorite_vulnerability(probs: list[float]) -> float:
    if not probs:
        return 0.0
    return 1.0 - max(probs)


def _group_qual_probs(group: str, qualify_probs: dict[str, float]) -> list[float]:
    return [qualify_probs.get(team, 0.0) for team in WC2026_GROUPS[group]]


def _pair_entropy(counts: Counter, total: int) -> float:
    if total <= 0 or not counts:
        return 0.0
    freqs = [count / total for count in counts.values() if count > 0]
    return -sum(freq * math.log(freq) for freq in freqs)


def _estimate_pair_entropy_from_marginals(
    group: str,
    qualify_probs: dict[str, float],
    n_samples: int,
    seed: int = RANDOM_SEED,
) -> float:
    """Approximate pair diversity by sampling 2 qualifiers weighted by qual%."""
    import random

    teams = WC2026_GROUPS[group]
    rng = random.Random(seed + ord(group[0]))
    counts: Counter = Counter()

    for _ in range(n_samples):
        pool = teams[:]
        weights = [qualify_probs.get(team, 0.0) for team in pool]
        picked: list[str] = []
        for _ in range(2):
            total = sum(weights)
            if total <= 0:
                break
            threshold = rng.random() * total
            cumulative = 0.0
            for index, weight in enumerate(weights):
                cumulative += weight
                if threshold <= cumulative:
                    picked.append(pool[index])
                    del pool[index]
                    del weights[index]
                    break
        if len(picked) == 2:
            counts[tuple(sorted(picked))] += 1

    return _pair_entropy(counts, n_samples)


def compute_qualifier_pair_entropies(
    n_simulations: int,
    qualify_probs: dict[str, float],
) -> tuple[dict[str, float], str]:
    try:
        df_matches, team_hist, elo_dict = load_and_preprocess("data")
        del df_matches
        models = load_models("models")

        feature_cache = build_feature_cache(team_hist, elo_dict)
        lambda_cache = build_lambda_cache(feature_cache, models)
        fixtures = get_group_fixtures()
        group_preds = [
            lambda_cache[(fixture["home_team"], fixture["away_team"])]
            for fixture in fixtures
        ]
        group_draws = _draw_group_stage_batch(group_preds, n_simulations, seed=RANDOM_SEED)

        pair_counts: dict[str, Counter] = {group: Counter() for group in WC2026_GROUPS}

        for sim_idx in range(n_simulations):
            group_standings, _ = _group_standings_from_batch(group_draws, sim_idx, fixtures)
            for group, standings_df in group_standings.items():
                top_two = sorted(
                    standings_df.loc[standings_df["rank"] <= 2, "team"].tolist()
                )
                if len(top_two) == 2:
                    pair_counts[group][tuple(top_two)] += 1

        return (
            {group: _pair_entropy(pair_counts[group], n_simulations) for group in WC2026_GROUPS},
            "mc_group_stage_replay",
        )
    except Exception as exc:
        print(f"MC pair replay unavailable ({exc.__class__.__name__}); using marginal sampling approx.")
        return (
            {
                group: _estimate_pair_entropy_from_marginals(group, qualify_probs, n_simulations)
                for group in WC2026_GROUPS
            },
            "marginal_weighted_sampling_approx",
        )


def pick_winner(scores: dict[str, float]) -> tuple[str, float]:
    group = max(scores, key=scores.get)
    return group, scores[group]


def main() -> None:
    pred = json.loads(PREDICTIONS_PATH.read_text(encoding="utf-8"))
    qualify_probs = pred.get("qualify_probs", {})
    n_simulations = int(pred.get("n_simulations", 0) or 0)

    print(f"Data: {PREDICTIONS_PATH}")
    print(f"n_simulations={n_simulations}")
    print()

    print("Computing qualifier-pair entropy...")
    pair_entropies, pair_method = compute_qualifier_pair_entropies(n_simulations, qualify_probs)
    print(f"Pair method: {pair_method}")
    print()

    methods: list[tuple[str, callable]] = [
        ("0_current_qual_variance", lambda g: _variance_score(_group_qual_probs(g, qualify_probs))),
        ("1_shannon_entropy", lambda g: _shannon_entropy(_group_qual_probs(g, qualify_probs))),
        ("2_favorite_vulnerability", lambda g: _favorite_vulnerability(_group_qual_probs(g, qualify_probs))),
        ("3_qualifier_pair_diversity", lambda g: pair_entropies.get(g, 0.0)),
    ]

    print("=== PER-GROUP SCORES ===")
    print(
        f"{'Grp':<4} {'Var':>7} {'Ent':>6} {'FavVuln':>7} {'PairEnt':>7}  Teams"
    )
    print("-" * 95)
    for group in sorted(WC2026_GROUPS):
        probs = _group_qual_probs(group, qualify_probs)
        teams = ", ".join(WC2026_GROUPS[group])
        print(
            f"{group:<4} "
            f"{_variance_score(probs):>7.4f} "
            f"{_shannon_entropy(probs):>6.3f} "
            f"{_favorite_vulnerability(probs):>7.3f} "
            f"{pair_entropies.get(group, 0.0):>7.3f}  "
            f"{teams}"
        )

    print()
    print("=== WINNER BY METHOD ===")
    for name, scorer in methods:
        scores = {group: scorer(group) for group in WC2026_GROUPS}
        winner, score = pick_winner(scores)
        teams = WC2026_GROUPS[winner]
        probs = {team: qualify_probs.get(team, 0.0) for team in teams}
        favorite = max(probs, key=probs.get)
        print(f"{name}: Group {winner} (score={score:.4f})")
        print(f"  teams: {teams}")
        print(f"  qual%: { {team: round(probs[team]*100, 1) for team in teams} }")
        if name == "2_favorite_vulnerability":
            print(f"  favorite: {favorite} ({probs[favorite]*100:.1f}% qual)")
        print()


if __name__ == "__main__":
    main()
