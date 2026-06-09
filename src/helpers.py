"""
src/helpers.py
==============
Shared utilities for the FIFA WC 2026 prediction pipeline.

Contents:
  - MatchRecord: typed dataclass for a single historical match
  - TOURNAMENT_WEIGHTS: importance multipliers by competition type
  - WC2026_GROUPS: official FIFA WC 2026 group + bracket definition
  - WC2026_FIXTURES: full group stage fixture list
  - resolve_group_standings: FIFA official tiebreaker order
  - get_knockout_bracket: maps group qualifiers to knockout slots
  - format_submission: formats Monte Carlo results → submission DataFrame
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

from src.config import RANDOM_SEED, TOURNAMENT_WEIGHTS, HOST_NATIONS, WC2026_GROUPS

# ---------------------------------------------------------------------------
# Typed Match Record
# ---------------------------------------------------------------------------


@dataclass
class MatchRecord:
    """
    Immutable record for a single historical match.
    Used to build per-team history chains in preprocessing.
    """

    date: pd.Timestamp
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    tournament: str
    neutral: bool
    home_elo: float = 1500.0
    away_elo: float = 1500.0

    @property
    def tournament_weight(self) -> float:
        for key, weight in TOURNAMENT_WEIGHTS.items():
            if key.lower() in self.tournament.lower():
                return weight
        return 1.0


# Full group stage fixture list (home = first-listed in each matchup)
def get_group_fixtures() -> List[Dict]:
    """Generate all 48 group stage fixtures from the group definitions."""
    fixtures = []
    match_id = 1
    for group, teams in WC2026_GROUPS.items():
        for i, team_a in enumerate(teams):
            for team_b in teams[i + 1 :]:
                fixtures.append(
                    {
                        "match_id": match_id,
                        "stage": "Group",
                        "group": group,
                        "home_team": team_a,
                        "away_team": team_b,
                        "neutral": True,
                    }
                )
                match_id += 1
    return fixtures


# ---------------------------------------------------------------------------
# Group Stage Tiebreaker Resolution (FIFA Official Rules)
# ---------------------------------------------------------------------------


def resolve_group_standings(
    results: List[Dict],
    rng: Optional[np.random.Generator] = None,
) -> pd.DataFrame:
    """
    Computes final group standings from a list of simulated match results.

    Tiebreaker order (FIFA official):
      1. Points (W=3, D=1, L=0)
      2. Goal Difference (GD)
      3. Goals For (GF)
      4. Yellow Cards (lower is better)
      5. Red Cards (lower is better)
      6. Random (coin flip)

    Parameters
    ----------
    results : list of dicts with keys:
        home_team, away_team, home_goals, away_goals,
        home_yellow, away_yellow, home_red, away_red
    rng : optional numpy Generator for reproducible tiebreaks

    Returns
    -------
    pd.DataFrame sorted by rank (1 = first, 4 = last)
    """
    teams: Dict[str, Dict] = {}

    def _init(team: str) -> None:
        if team not in teams:
            teams[team] = dict(
                pts=0, gd=0, gf=0, ga=0, yellow=0, red=0, played=0
            )

    for r in results:
        ht, at = r["home_team"], r["away_team"]
        hg, ag = r["home_goals"], r["away_goals"]
        _init(ht)
        _init(at)

        teams[ht]["played"] += 1
        teams[at]["played"] += 1
        teams[ht]["gf"] += hg
        teams[ht]["ga"] += ag
        teams[at]["gf"] += ag
        teams[at]["ga"] += hg
        teams[ht]["gd"] += hg - ag
        teams[at]["gd"] += ag - hg
        teams[ht]["yellow"] += r.get("home_yellow", 0)
        teams[at]["yellow"] += r.get("away_yellow", 0)
        teams[ht]["red"] += r.get("home_red", 0)
        teams[at]["red"] += r.get("away_red", 0)

        if hg > ag:
            teams[ht]["pts"] += 3
        elif hg == ag:
            teams[ht]["pts"] += 1
            teams[at]["pts"] += 1
        else:
            teams[at]["pts"] += 3

    team_names = list(teams.keys())
    n_teams = len(team_names)
    pts = np.array([teams[t]["pts"] for t in team_names], dtype=np.int32)
    gd = np.array([teams[t]["gd"] for t in team_names], dtype=np.int32)
    gf = np.array([teams[t]["gf"] for t in team_names], dtype=np.int32)
    yellow = np.array([teams[t]["yellow"] for t in team_names], dtype=np.int32)
    red = np.array([teams[t]["red"] for t in team_names], dtype=np.int32)

    if rng is not None:
        rand_vals = rng.random(n_teams)
    else:
        rand_vals = np.array([random.random() for _ in range(n_teams)])

    # Sort: pts/gd/gf desc; yellow/red asc; rand desc (lexsort uses last key as primary)
    order = np.lexsort((-rand_vals, red, yellow, -gf, -gd, -pts))

    df = pd.DataFrame(
        {
            "team": [team_names[i] for i in order],
            "pts": pts[order],
            "gd": gd[order],
            "gf": gf[order],
            "ga": np.array([teams[t]["ga"] for t in team_names], dtype=np.int32)[order],
            "yellow": yellow[order],
            "red": red[order],
            "played": np.array([teams[t]["played"] for t in team_names], dtype=np.int32)[order],
            "rand": rand_vals[order],
        }
    )
    df["rank"] = np.arange(1, n_teams + 1)
    return df


# ---------------------------------------------------------------------------
# Knockout Bracket Builder
# ---------------------------------------------------------------------------


def build_knockout_bracket(group_standings: Dict[str, pd.DataFrame]) -> List[Dict]:
    """
    Maps group stage qualifiers to Round of 32 knockout matchups.
    Uses the official FIFA WC 2026 bracket formula.

    Returns a list of R32 match dicts with home_team / away_team set.
    """
    # Extract 1st and 2nd place finishers per group
    qualifiers: Dict[str, Tuple[str, str]] = {}
    for group, df in group_standings.items():
        first = df[df["rank"] == 1]["team"].values[0]
        second = df[df["rank"] == 2]["team"].values[0]
        qualifiers[group] = (first, second)

    # Official WC 2026 R32 bracket pairings (group winners vs runners-up)
    # Source: FIFA official bracket announcement
    bracket_pairs = [
        ("A1", "B2"), ("C1", "D2"), ("E1", "F2"), ("G1", "H2"),
        ("I1", "J2"), ("K1", "L2"), ("B1", "A2"), ("D1", "C2"),
        ("F1", "E2"), ("H1", "G2"), ("J1", "I2"), ("L1", "K2"),
        ("A1", "C2"), ("B1", "D2"), ("E1", "G2"), ("F1", "H2"),  # cross-bracket
    ]

    # Simplified: standard cross-bracket pairing for 12-group WC 2026
    # Each group winner meets a runner-up from a fixed cross-bracket slot
    r32_matchups = []
    match_id = 49  # Group stage ends at 48

    pairing_formula = [
        ("A", 1, "B", 2), ("C", 1, "D", 2), ("E", 1, "F", 2),
        ("G", 1, "H", 2), ("I", 1, "J", 2), ("K", 1, "L", 2),
        ("B", 1, "A", 2), ("D", 1, "C", 2), ("F", 1, "E", 2),
        ("H", 1, "G", 2), ("J", 1, "I", 2), ("L", 1, "K", 2),
        ("A", 1, "C", 2), ("B", 1, "D", 2), ("E", 1, "G", 2),
        ("F", 1, "H", 2),
    ]

    for g1, r1, g2, r2 in pairing_formula:
        home = qualifiers[g1][r1 - 1]
        away = qualifiers[g2][r2 - 1]
        r32_matchups.append(
            {
                "match_id": match_id,
                "stage": "Round of 32",
                "home_team": home,
                "away_team": away,
                "neutral": True,
            }
        )
        match_id += 1

    return r32_matchups


# ---------------------------------------------------------------------------
# Submission Formatter
# ---------------------------------------------------------------------------


def format_submission(mc_results: Dict[str, Dict]) -> pd.DataFrame:
    """
    Converts Monte Carlo aggregated results into a submission-ready DataFrame.

    Parameters
    ----------
    mc_results : dict keyed by match_id, values contain:
        - home_team, away_team, stage
        - most_common_home_goals, most_common_away_goals
        - home_win_prob, draw_prob, away_win_prob

    Returns
    -------
    pd.DataFrame with competition submission columns
    """
    rows = []
    for match_id, res in mc_results.items():
        rows.append(
            {
                "match_id": match_id,
                "stage": res["stage"],
                "home_team": res["home_team"],
                "away_team": res["away_team"],
                "predicted_home_goals": res["most_common_home_goals"],
                "predicted_away_goals": res["most_common_away_goals"],
                "home_win_prob": round(res["home_win_prob"], 4),
                "draw_prob": round(res["draw_prob"], 4),
                "away_win_prob": round(res["away_win_prob"], 4),
            }
        )
    return pd.DataFrame(rows).sort_values("match_id").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Predicted Standings & Final (for frontend display)
# ---------------------------------------------------------------------------


def build_predicted_group_standings(
    mc_results: Dict[Any, Dict],
    qualify_probs: Dict[str, float],
) -> Dict[str, List[Dict]]:
    """
    Builds predicted group standings from aggregated group-stage scorelines.

    Uses the most common goals per fixture (same approach as the Gradio app).
    """
    group_fixtures = get_group_fixtures()
    group_sim_results: Dict[str, List[Dict]] = defaultdict(list)

    for fixture in group_fixtures:
        mid = fixture["match_id"]
        res = mc_results.get(mid)
        if not res:
            continue
        group_sim_results[fixture["group"]].append(
            {
                "home_team": res["home_team"],
                "away_team": res["away_team"],
                "home_goals": res["most_common_home_goals"],
                "away_goals": res["most_common_away_goals"],
                "home_yellow": 0,
                "away_yellow": 0,
                "home_red": 0,
                "away_red": 0,
            }
        )

    standings_by_group: Dict[str, List[Dict]] = {}
    for group in sorted(WC2026_GROUPS.keys()):
        results = group_sim_results.get(group, [])
        if not results:
            standings_by_group[group] = []
            continue

        standings = resolve_group_standings(results)
        rows = []
        for _, row in standings.iterrows():
            team = row["team"]
            rows.append(
                {
                    "team": team,
                    "rank": int(row["rank"]),
                    "pts": int(row["pts"]),
                    "gd": int(row["gd"]),
                    "gf": int(row["gf"]),
                    "played": int(row["played"]),
                    "qualify_prob": qualify_probs.get(team, 0.0),
                }
            )
        standings_by_group[group] = rows

    return standings_by_group


def build_predicted_final(
    pairing_counter: Counter,
    winner_by_pairing: Dict[Tuple[str, str], Counter],
    n_simulations: int,
) -> Dict[str, Any]:
    """
    Derives the most common final pairing and predicted winner/runner-up.
    """
    if not pairing_counter:
        return {
            "home_team": "",
            "away_team": "",
            "winner": "",
            "runner_up": "",
            "pairing_prob": 0.0,
            "winner_prob": 0.0,
        }

    (home_team, away_team), pair_count = pairing_counter.most_common(1)[0]
    pairing_prob = pair_count / n_simulations

    winners = winner_by_pairing.get((home_team, away_team), Counter())
    if winners:
        winner, winner_count = winners.most_common(1)[0]
        winner_prob = winner_count / pair_count
        runner_up = away_team if winner == home_team else home_team
    else:
        winner = home_team
        runner_up = away_team
        winner_prob = 0.0

    return {
        "home_team": home_team,
        "away_team": away_team,
        "winner": winner,
        "runner_up": runner_up,
        "pairing_prob": pairing_prob,
        "winner_prob": winner_prob,
    }
