"""
src/wrapped_awards.py
=====================
Build display-ready World Cup Wrapped award cards from simulation output.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from src.config import WC2026_GROUPS


def _parse_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_elo(team_stats: Dict[str, Dict[str, str]], team: str) -> int:
    return int(_parse_float(team_stats.get(team, {}).get("FIFA ELO Rating", "1500"), 1500))


def _rank_map(items: Dict[str, float], descending: bool = True) -> Dict[str, int]:
    ordered = sorted(
        items.items(),
        key=lambda item: (-item[1], item[0]) if descending else (item[1], item[0]),
    )
    return {team: index + 1 for index, (team, _) in enumerate(ordered)}


def _pct(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def _signed(value: float, digits: int = 1) -> str:
    prefix = "+" if value > 0 else ""
    return f"{prefix}{value:.{digits}f}"


def _build_dark_horse(
    champion_probs: Dict[str, float],
    team_stats: Dict[str, Dict[str, str]],
) -> Dict[str, Any]:
    if not team_stats:
        return {}

    elo_ranks = _rank_map(
        {team: _parse_elo(team_stats, team) for team in team_stats},
        descending=True,
    )
    champion_ranks = _rank_map(champion_probs or {}, descending=True)

    best_team = ""
    best_gap = float("-inf")
    for team in team_stats:
        champ_rank = champion_ranks.get(team)
        if champ_rank is None:
            continue
        gap = elo_ranks[team] - champ_rank
        if gap > best_gap:
            best_gap = gap
            best_team = team

    if not best_team:
        return {}

    champ_prob = champion_probs.get(best_team, 0.0)
    elo_rank = elo_ranks[best_team]
    return {
        "id": "dark-horse",
        "bigNumber": _signed(best_gap, 1),
        "statLabel": "spots above their ELO rank",
        "teams": [best_team],
        "teamName": best_team,
        "insight": (
            f"Model gives them {_pct(champ_prob)} champ odds while ELO rank is #{elo_rank}"
        ),
    }


def _build_giant_killer(
    team_upset_counts: Dict[str, int],
    n_simulations: int,
) -> Dict[str, Any]:
    if not team_upset_counts or n_simulations <= 0:
        return {}

    best_team, upset_count = max(team_upset_counts.items(), key=lambda item: item[1])
    avg_upsets = upset_count / n_simulations
    upset_rate = upset_count / max(
        sum(team_upset_counts.values()),
        1,
    )

    return {
        "id": "giant-killer",
        "bigNumber": f"{avg_upsets:.1f}",
        "statLabel": "avg. upsets per simulation",
        "teams": [best_team],
        "teamName": best_team,
        "insight": (
            f"Beat higher-ELO opponents in {_pct(upset_rate)} of their simulated knockouts"
        ),
    }


def _build_lethal_attack(team_stats: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    if not team_stats:
        return {}

    best_team = max(
        team_stats,
        key=lambda team: _parse_float(
            team_stats[team].get("ELO-Adjusted Attack Score", "0")
        ),
    )
    raw_attack = _parse_float(
        team_stats[best_team].get(
            "Rolling Attack Rate",
            team_stats[best_team].get("Attack Strength (Avg Goals)", "0"),
        )
    )
    match_count = int(
        _parse_float(team_stats[best_team].get("Rolling Match Count", "0"))
    )
    last5_goals = int(
        _parse_float(team_stats[best_team].get("Last 5 Goals Scored", "0"))
    )
    team_elo = _parse_elo(team_stats, best_team)

    return {
        "id": "lethal-attack",
        "bigNumber": f"{raw_attack:.2f}",
        "statLabel": "expected goals per game",
        "teams": [best_team],
        "teamName": best_team,
        "insight": (
            f"Scored {last5_goals} goals in their last 5 matches "
            f"({raw_attack:.2f} goals/game over {match_count} matches at ELO {team_elo})"
        ),
    }


def _build_fortress(team_stats: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    if not team_stats:
        return {}

    best_team = min(
        team_stats,
        key=lambda team: _parse_float(
            team_stats[team].get("ELO-Adjusted Fortress Score", "999")
        ),
    )
    raw_conceded = _parse_float(
        team_stats[best_team].get(
            "Rolling Conceded Rate",
            team_stats[best_team].get("Expected Conceded Goals", "0"),
        )
    )
    match_count = int(
        _parse_float(team_stats[best_team].get("Rolling Match Count", "0"))
    )
    avg_opponent_elo = int(
        _parse_float(team_stats[best_team].get("Avg Opponent ELO (Rolling)", "1500"))
    )
    team_elo = _parse_elo(team_stats, best_team)

    return {
        "id": "fortress",
        "bigNumber": f"{raw_conceded:.2f}",
        "statLabel": "goals conceded per game",
        "teams": [best_team],
        "teamName": best_team,
        "insight": (
            f"Allowed {raw_conceded:.2f} goals per match over {match_count} matches "
            f"against avg opponent ELO {avg_opponent_elo} (team ELO {team_elo})"
        ),
    }


def _group_elos(
    group: str,
    team_stats: Dict[str, Dict[str, str]],
) -> List[int]:
    teams = WC2026_GROUPS.get(group, [])
    return [_parse_elo(team_stats, team) for team in teams if team in team_stats]


def _group_top3_avg_elo(
    group: str,
    team_stats: Dict[str, Dict[str, str]],
) -> float:
    elos = sorted(_group_elos(group, team_stats), reverse=True)
    if not elos:
        return 0.0
    top_three = elos[:3]
    return sum(top_three) / len(top_three)


def _build_group_of_death(team_stats: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    if not team_stats:
        return {}

    best_group = max(WC2026_GROUPS, key=lambda group: _group_top3_avg_elo(group, team_stats))
    teams = WC2026_GROUPS[best_group]
    top3_avg = _group_top3_avg_elo(best_group, team_stats)
    top_three = sorted(
        teams,
        key=lambda team: _parse_elo(team_stats, team),
        reverse=True,
    )[:3]

    return {
        "id": "group-of-death",
        "bigNumber": f"{top3_avg:.0f}",
        "statLabel": "avg. ELO of top 3 teams",
        "teams": teams,
        "badgeLabel": f"Group {best_group}",
        "insight": f"Top 3: {', '.join(top_three)} — avg ELO {top3_avg:.0f}",
    }


def _group_chaos_entropy(
    group: str,
    qualify_probs: Dict[str, float],
) -> float:
    teams = WC2026_GROUPS.get(group, [])
    probs = [qualify_probs.get(team, 0.0) for team in teams]
    total = sum(probs)
    if total <= 0:
        return 0.0
    normalized = [prob / total for prob in probs if prob > 0]
    return -sum(prob * math.log(prob) for prob in normalized)


def _group_chaos_insight(
    group: str,
    qualify_probs: Dict[str, float],
    group_standings: Dict[str, List[Dict[str, Any]]],
) -> str:
    teams = WC2026_GROUPS.get(group, [])
    if not teams:
        return "Most unpredictable qualification outlook of any group"

    favorite = max(teams, key=lambda team: qualify_probs.get(team, 0.0))
    favorite_prob = qualify_probs.get(favorite, 0.0)
    if favorite_prob < 1.0:
        return f"Even the group favorite ({favorite}) only has {_pct(favorite_prob)} qual chance"

    rows = group_standings.get(group, [])
    if len(rows) >= 3:
        by_rank = sorted(rows, key=lambda row: row.get("rank", 99))
        first = by_rank[0]
        third = by_rank[2]
        first_prob = float(first.get("qualify_prob", 0.0))
        third_prob = float(third.get("qualify_prob", 0.0))
        if third_prob > first_prob:
            return (
                f"3rd place {third['team']} ({_pct(third_prob)}) has higher qual% than "
                f"1st place {first['team']} ({_pct(first_prob)})"
            )

    return f"Highest qualification uncertainty across {', '.join(teams[:2])} and peers"


def _build_group_of_chaos(
    qualify_probs: Dict[str, float],
    group_standings: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    if not qualify_probs:
        return {}

    best_group = max(
        WC2026_GROUPS,
        key=lambda group: _group_chaos_entropy(group, qualify_probs),
    )
    teams = WC2026_GROUPS[best_group]
    entropy = _group_chaos_entropy(best_group, qualify_probs)
    insight = _group_chaos_insight(best_group, qualify_probs, group_standings)

    return {
        "id": "group-of-chaos",
        "bigNumber": f"{entropy:.2f}",
        "statLabel": "qualification entropy",
        "teams": teams,
        "badgeLabel": f"Group {best_group}",
        "insight": insight,
    }


def build_wrapped_awards(
    mc_output: dict,
    team_stats: dict,
    n_simulations: int,
) -> List[Dict[str, Any]]:
    """Compute six wrapped award cards from Monte Carlo output and team stats."""
    champion_probs = mc_output.get("champion_probs", {})
    qualify_probs = mc_output.get("qualify_probs", {})
    group_standings = mc_output.get("group_standings", {})
    team_upset_counts = mc_output.get("team_upset_counts", {})

    builders = [
        lambda: _build_dark_horse(champion_probs, team_stats),
        lambda: _build_giant_killer(team_upset_counts, n_simulations),
        lambda: _build_lethal_attack(team_stats),
        lambda: _build_fortress(team_stats),
        lambda: _build_group_of_death(team_stats),
        lambda: _build_group_of_chaos(qualify_probs, group_standings),
    ]

    awards: List[Dict[str, Any]] = []
    for build in builders:
        card = build()
        if card:
            awards.append(card)
    return awards
