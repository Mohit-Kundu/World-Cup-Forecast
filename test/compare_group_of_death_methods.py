"""Compare Group of Death scoring methods against predictions.json."""

from __future__ import annotations

import json
import math
from itertools import combinations
from pathlib import Path

from src.config import WC2026_GROUPS

PREDICTIONS_PATH = Path("output/predictions.json")


def elos_for_group(team_stats: dict, group: str) -> list[int]:
    return [
        int(team_stats[team]["FIFA ELO Rating"])
        for team in WC2026_GROUPS[group]
        if team in team_stats
    ]


def mean_elo(elos: list[int]) -> float:
    return sum(elos) / len(elos)


def min_elo(elos: list[int]) -> float:
    return float(min(elos))


def mean_minus_std(elos: list[int]) -> float:
    mean = mean_elo(elos)
    variance = sum((elo - mean) ** 2 for elo in elos) / len(elos)
    return mean - math.sqrt(variance)


def top3_avg(elos: list[int]) -> float:
    top = sorted(elos, reverse=True)[:3]
    return sum(top) / len(top)


def pairwise_score(elos: list[int]) -> float:
    return sum((a + b) / (1 + abs(a - b)) for a, b in combinations(elos, 2))


def qualify_entropy(group: str, qualify_probs: dict[str, float]) -> float:
    probs = [qualify_probs.get(team, 0.0) for team in WC2026_GROUPS[group]]
    total = sum(probs)
    if total <= 0:
        return 0.0
    normalized = [prob / total for prob in probs if prob > 0]
    return -sum(prob * math.log(prob) for prob in normalized)


def hybrid_score(elos: list[int]) -> float:
    ordered = sorted(elos, reverse=True)
    top3_average = sum(ordered[:3]) / 3
    minimum = ordered[-1]
    spread = ordered[0] - ordered[-1]
    return top3_average + 0.5 * minimum - 0.3 * spread


def pick_winner(scores: dict[str, float]) -> tuple[str, float]:
    group = max(scores, key=scores.get)
    return group, scores[group]


def main() -> None:
    pred = json.loads(PREDICTIONS_PATH.read_text(encoding="utf-8"))
    team_stats = pred.get("team_stats", {})
    qualify_probs = pred.get("qualify_probs", {})

    methods: list[tuple[str, callable]] = [
        ("0_current_mean_elo", lambda g: mean_elo(elos_for_group(team_stats, g))),
        ("1_min_elo_weakest_link", lambda g: min_elo(elos_for_group(team_stats, g))),
        ("2_mean_minus_std", lambda g: mean_minus_std(elos_for_group(team_stats, g))),
        ("3_top3_avg", lambda g: top3_avg(elos_for_group(team_stats, g))),
        ("4_pairwise_competitiveness", lambda g: pairwise_score(elos_for_group(team_stats, g))),
        ("5_qualify_entropy", lambda g: qualify_entropy(g, qualify_probs)),
        ("6_hybrid_recommended", lambda g: hybrid_score(elos_for_group(team_stats, g))),
    ]

    print(f"Data: {PREDICTIONS_PATH}")
    print(f"n_simulations={pred.get('n_simulations')}")
    print()

    print("=== PER-GROUP SCORES ===")
    print(f"{'Grp':<4} {'Mean':>6} {'Min':>6} {'Top3':>6} {'M-Std':>6} {'Pair':>7} {'Ent':>5}  Teams")
    print("-" * 100)
    for group in sorted(WC2026_GROUPS):
        elos = elos_for_group(team_stats, group)
        if len(elos) < 4:
            continue
        teams = WC2026_GROUPS[group]
        print(
            f"{group:<4} "
            f"{mean_elo(elos):>6.0f} "
            f"{min(elos):>6} "
            f"{top3_avg(elos):>6.0f} "
            f"{mean_minus_std(elos):>6.0f} "
            f"{pairwise_score(elos):>7.1f} "
            f"{qualify_entropy(group, qualify_probs):>5.2f}  "
            f"{', '.join(teams)}"
        )

    print()
    print("=== WINNER BY METHOD ===")
    for name, scorer in methods:
        scores = {
            group: scorer(group)
            for group in WC2026_GROUPS
            if len(elos_for_group(team_stats, group)) == 4
        }
        winner, score = pick_winner(scores)
        teams = WC2026_GROUPS[winner]
        group_elos = elos_for_group(team_stats, winner)
        elo_map = dict(zip(teams, group_elos))
        print(f"{name}: Group {winner} (score={score:.2f})")
        print(f"  teams: {teams}")
        print(f"  elos:  {elo_map}")
        print()


if __name__ == "__main__":
    main()
