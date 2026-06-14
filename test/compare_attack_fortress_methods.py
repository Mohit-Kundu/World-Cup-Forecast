"""Compare current vs ELO-adjusted lethal attack / fortress scoring."""

from __future__ import annotations

import json
from pathlib import Path

from src.config import TOURNAMENT_DATE, WC2026_GROUPS
from src.feature_engineering import build_team_history_dfs, get_team_rolling_profile
from src.predictions_io import build_team_stats
from src.preprocessing import load_and_preprocess

PREDICTIONS_PATH = Path("output/predictions.json")
ELO_WEIGHT = 5


def _all_teams() -> list[str]:
    return [team for teams in WC2026_GROUPS.values() for team in teams]


def _build_profiles(team_stats: dict) -> dict[str, dict]:
    _, team_hist, elo_dict = load_and_preprocess("data")
    team_dfs = build_team_history_dfs(team_hist)
    profiles: dict[str, dict] = {}

    for team in _all_teams():
        if team not in team_stats:
            continue
        stats = team_stats[team]
        profile = get_team_rolling_profile(
            team_dfs.get(team), TOURNAMENT_DATE, window=10
        )
        games = int(profile["match_count"])
        goals_scored = float(profile["goals_scored"])
        goals_conceded = float(profile["goals_conceded"])
        profiles[team] = {
            "elo": float(stats["FIFA ELO Rating"]),
            "games": games,
            "rolling_attack": goals_scored / games if games else 0.0,
            "rolling_conceded": goals_conceded / games if games else 0.0,
            "smoothed_attack": float(stats.get("ELO-Adjusted Attack Score", "0")),
            "smoothed_conceded": float(stats.get("ELO-Adjusted Fortress Score", "0")),
            "raw_attack": float(stats.get("Rolling Attack Rate", "0")),
            "raw_conceded": float(stats.get("Rolling Conceded Rate", "0")),
        }

    return profiles


def _mean_elo(profiles: dict[str, dict]) -> float:
    elos = [item["elo"] for item in profiles.values()]
    return sum(elos) / len(elos) if elos else 1500.0


def _current_attack_winner(profiles: dict[str, dict], team_stats: dict) -> tuple[str, float]:
    team = max(
        team_stats,
        key=lambda name: float(team_stats[name].get("ELO-Adjusted Attack Score", "0")),
    )
    return team, float(team_stats[team]["ELO-Adjusted Attack Score"])


def _current_fortress_winner(profiles: dict[str, dict], team_stats: dict) -> tuple[str, float]:
    team = min(
        team_stats,
        key=lambda name: float(team_stats[name].get("ELO-Adjusted Fortress Score", "999")),
    )
    return team, float(team_stats[team]["ELO-Adjusted Fortress Score"])


def _elo_adjusted_attack_score(
    team: str,
    profiles: dict[str, dict],
    global_avg_attack: float,
    mean_elo: float,
) -> float:
    item = profiles[team]
    raw_rate = item["rolling_attack"]
    games = item["games"]
    smoothed = (raw_rate * games + (global_avg_attack * ELO_WEIGHT)) / (games + ELO_WEIGHT)
    return smoothed * (item["elo"] / mean_elo)


def _elo_adjusted_fortress_score(
    team: str,
    profiles: dict[str, dict],
    global_avg_conceded: float,
    mean_elo: float,
) -> float:
    item = profiles[team]
    raw_rate = item["rolling_conceded"]
    games = item["games"]
    smoothed = (raw_rate * games + (global_avg_conceded * ELO_WEIGHT)) / (games + ELO_WEIGHT)
    return smoothed * (mean_elo / item["elo"])


def main() -> None:
    pred = json.loads(PREDICTIONS_PATH.read_text(encoding="utf-8"))
    team_stats = pred["team_stats"]
    profiles = _build_profiles(team_stats)

    mean_elo = _mean_elo(profiles)
    global_avg_attack = sum(item["rolling_attack"] for item in profiles.values()) / len(profiles)
    global_avg_conceded = sum(item["rolling_conceded"] for item in profiles.values()) / len(profiles)

    current_attack_team, current_attack_score = _current_attack_winner(profiles, team_stats)
    current_fortress_team, current_fortress_score = _current_fortress_winner(profiles, team_stats)

    elo_attack_scores = {
        team: _elo_adjusted_attack_score(team, profiles, global_avg_attack, mean_elo)
        for team in profiles
    }
    elo_fortress_scores = {
        team: _elo_adjusted_fortress_score(team, profiles, global_avg_conceded, mean_elo)
        for team in profiles
    }

    new_attack_team = max(elo_attack_scores, key=elo_attack_scores.get)
    new_fortress_team = min(elo_fortress_scores, key=elo_fortress_scores.get)

    print(f"Data: {PREDICTIONS_PATH}")
    print(f"Teams compared: {len(profiles)}")
    print(f"Mean ELO: {mean_elo:.0f}")
    print(f"Global avg attack rate: {global_avg_attack:.3f}")
    print(f"Global avg conceded rate: {global_avg_conceded:.3f}")
    print()

    print("=== LETHAL ATTACK (ELO-adjusted Bayesian) ===")
    print(
        f"Winner: {current_attack_team} "
        f"(score={current_attack_score:.3f}, raw={profiles[current_attack_team]['rolling_attack']:.2f})"
    )

    print()
    print("Top 5 current smoothed attack:")
    for team, _ in sorted(
        profiles.items(), key=lambda item: item[1]["smoothed_attack"], reverse=True
    )[:5]:
        print(
            f"  {team:<18} raw={profiles[team]['rolling_attack']:.2f} "
            f"smoothed={profiles[team]['smoothed_attack']:.2f} "
            f"elo={profiles[team]['elo']:.0f} "
            f"elo_adj={elo_attack_scores[team]:.3f}"
        )

    print()
    print("=== FORTRESS DEFENSE ===")
    print(
        f"Current (Bayesian only): {current_fortress_team} "
        f"(smoothed={current_fortress_score:.2f}, raw={profiles[current_fortress_team]['rolling_conceded']:.2f})"
    )
    print(
        f"ELO-adjusted:            {new_fortress_team} "
        f"(score={elo_fortress_scores[new_fortress_team]:.3f}, raw={profiles[new_fortress_team]['rolling_conceded']:.2f})"
    )
    if current_fortress_team != new_fortress_team:
        print("  -> WINNER CHANGES")
    else:
        print("  -> same winner")

    print()
    print("Top 5 current smoothed conceded (lower = better fortress):")
    for team, _ in sorted(
        profiles.items(), key=lambda item: item[1]["smoothed_conceded"]
    )[:5]:
        print(
            f"  {team:<18} raw={profiles[team]['rolling_conceded']:.2f} "
            f"smoothed={profiles[team]['smoothed_conceded']:.2f} "
            f"elo={profiles[team]['elo']:.0f} "
            f"elo_adj={elo_fortress_scores[team]:.3f}"
        )

    print()
    print("=== BIG NUMBER ON CARD (raw rate, per spec) ===")
    print(
        f"Attack card would show: {profiles[new_attack_team]['rolling_attack']:.2f} goals/game ({new_attack_team})"
    )
    print(
        f"Fortress card would show: {profiles[new_fortress_team]['rolling_conceded']:.2f} conceded/game ({new_fortress_team})"
    )


if __name__ == "__main__":
    main()
