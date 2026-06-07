"""
src/feature_engineering.py
===========================
Feature matrix construction for the WC 2026 prediction models.

Implements all features from the architecture spec plus:
  - Improvement #1: compute_recency_weights (used in models.py)
  - Improvement #2: get_team_form (rolling W/D/L form index)
  - Improvement #3: get_h2h_features (historical matchup stats)
  - Improvement #4: compute_dynamic_discipline (data-driven card proxy)

Public API:
  compute_recency_weights(df) -> np.ndarray
  build_feature_matrix(df_matches, team_hist) -> pd.DataFrame
  build_prediction_row(home_team, away_team, team_hist, elo_df, match_date) -> pd.Series
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.helpers import MatchRecord
from src.config import HOST_NATIONS, TOURNAMENT_WEIGHTS, FEATURE_COLS

logger = logging.getLogger(__name__)



# ---------------------------------------------------------------------------
# Improvement #1 — Recency Weights
# ---------------------------------------------------------------------------


def compute_recency_weights(
    df: pd.DataFrame,
    current_year: int = 2026,
    half_life_years: float = 15.0,
) -> np.ndarray:
    """
    Computes exponential decay sample weights for historical matches.

    Matches closer to the tournament year receive weights closer to 1.0.
    Older matches receive lower weights (min floor: 0.05).

    Parameters
    ----------
    df              : DataFrame with a 'date' column
    current_year    : reference year (default: 2026)
    half_life_years : years for weight to halve (default: 15)

    Returns
    -------
    np.ndarray of shape (len(df),) with values in [0.05, 1.0]
    """
    dates = pd.to_datetime(df["date"])
    years_elapsed = current_year - dates.dt.year
    weights = np.exp(-np.log(2) * years_elapsed / half_life_years)
    return np.clip(weights, 0.05, 1.0)


# ---------------------------------------------------------------------------
# Rolling Attack / Defence Rates
# ---------------------------------------------------------------------------


def _get_rolling_rates(
    history: List[MatchRecord],
    team: str,
    current_date: pd.Timestamp,
    window: int = 10,
) -> Tuple[float, float]:
    """
    Computes weighted rolling attack and defence rates for a team.

    Returns (attack_rate, defense_rate) where:
      - attack_rate  = avg goals scored
      - defense_rate = 1 / (avg goals conceded + ε)  [higher = stronger defense]

    Scheme from spec:
      - ≤5 games:  linear interpolation with neutral rate 1.0
      - 6–10 games: last 5 weighted 70%, prior 5 weighted 30%
    """
    past = [h for h in history if h.date < current_date]
    if not past:
        return 1.0, 1.0

    recent = past[-window:]
    n = len(recent)

    scored = []
    conceded = []
    for h in recent:
        if h.home_team == team:
            scored.append(h.home_score)
            conceded.append(h.away_score)
        else:
            scored.append(h.away_score)
            conceded.append(h.home_score)

    if n <= 5:
        # Linear interpolation with neutral rate (weight = n/5)
        blend = n / 5.0
        attack = blend * np.mean(scored) + (1 - blend) * 1.0
        defence_conceded = blend * np.mean(conceded) + (1 - blend) * 1.0
    else:
        # Last 5 games: 70%, prior games: 30%
        recent5 = scored[-5:]
        prior = scored[:-5] if len(scored) > 5 else scored
        attack = 0.70 * np.mean(recent5) + 0.30 * np.mean(prior)

        recent5c = conceded[-5:]
        priorc = conceded[:-5] if len(conceded) > 5 else conceded
        defence_conceded = 0.70 * np.mean(recent5c) + 0.30 * np.mean(priorc)

    # Defense rate: invert conceded (higher is better)
    defense_rate = 1.0 / max(defence_conceded, 0.1)
    return float(attack), float(defense_rate)


# ---------------------------------------------------------------------------
# Improvement #2 — Rolling Form (Streak) Feature
# ---------------------------------------------------------------------------


def get_team_form(
    team_hist: Dict[str, List[MatchRecord]],
    team: str,
    current_date: pd.Timestamp,
    window: int = 5,
) -> float:
    """
    Computes a form index based on points earned in the team's last N matches.

    Returns a value in [0.0, 1.0]:
      - 1.0 = maximum form (all wins in last N games)
      - 0.0 = rock-bottom form (all losses)
      - Neutral default: 0.5 (no history)

    Parameters
    ----------
    team_hist    : dict of team -> list[MatchRecord]
    team         : team to compute form for
    current_date : only consider matches before this date
    window       : number of recent matches to consider
    """
    history = team_hist.get(team, [])
    history = [h for h in history if h.date < current_date]

    if not history:
        return 0.5  # Neutral default

    recent = history[-window:]
    points = []

    for h in recent:
        if h.home_team == team:
            if h.home_score > h.away_score:
                points.append(3)
            elif h.home_score == h.away_score:
                points.append(1)
            else:
                points.append(0)
        else:
            if h.away_score > h.home_score:
                points.append(3)
            elif h.away_score == h.home_score:
                points.append(1)
            else:
                points.append(0)

    # Scale average points per match from [0, 3] → [0, 1]
    return float(np.mean(points)) / 3.0 if points else 0.5


# ---------------------------------------------------------------------------
# Improvement #3 — Head-to-Head (H2H) Features
# ---------------------------------------------------------------------------


def get_h2h_features(
    team_hist: Dict[str, List[MatchRecord]],
    team_a: str,
    team_b: str,
    current_date: pd.Timestamp,
    max_lookback_years: float = 15.0,
) -> Tuple[float, float]:
    """
    Retrieves historical H2H stats between team_a (home) and team_b (away).

    Returns
    -------
    (win_rate, avg_goal_diff) from team_a's perspective:
      - win_rate:      fraction of matches team_a won [0.0, 1.0]
      - avg_goal_diff: mean (team_a goals − team_b goals) in H2H matches
    Neutral defaults: (0.5, 0.0)
    """
    history_a = team_hist.get(team_a, [])
    current_dt = pd.Timestamp(current_date)
    h2h_matches = []

    for h in history_a:
        if h.date >= current_dt:
            continue
        years_ago = (current_dt - h.date).days / 365.25
        if years_ago > max_lookback_years:
            continue
        opponents = {h.home_team, h.away_team}
        if team_b in opponents:
            h2h_matches.append(h)

    if not h2h_matches:
        return 0.5, 0.0

    wins = 0.0
    goal_diffs = []

    for h in h2h_matches:
        if h.home_team == team_a:
            goal_diffs.append(h.home_score - h.away_score)
            if h.home_score > h.away_score:
                wins += 1
            elif h.home_score == h.away_score:
                wins += 0.5
        else:
            goal_diffs.append(h.away_score - h.home_score)
            if h.away_score > h.home_score:
                wins += 1
            elif h.away_score == h.home_score:
                wins += 0.5

    win_rate = wins / len(h2h_matches)
    avg_gd = float(np.mean(goal_diffs))
    return float(win_rate), avg_gd


# ---------------------------------------------------------------------------
# Improvement #4 — Dynamic Discipline Rating Proxy
# ---------------------------------------------------------------------------


def compute_dynamic_discipline(
    team_hist: Dict[str, List[MatchRecord]],
    team: str,
    current_date: pd.Timestamp,
    window: int = 15,
) -> float:
    """
    Computes a dynamic discipline rate proxy (expected yellow cards per game).

    Replaces the hardcoded TEAM_DISCIPLINE lookup dict from the original pipeline.
    Teams that concede more goals (defending under pressure) tend to commit more fouls.

    Formula: discipline_proxy = 1.0 + (avg_conceded * 1.2), clipped to [0.5, 4.5]
    Baseline default: 2.0

    Parameters
    ----------
    team_hist    : dict of team -> list[MatchRecord]
    team         : team to compute discipline for
    current_date : only consider matches before this date
    window       : number of recent matches to look back
    """
    history = team_hist.get(team, [])
    history = [h for h in history if h.date < current_date]

    if not history:
        return 2.0  # Global baseline default

    recent = history[-window:]
    goals_conceded = []

    for h in recent:
        if h.home_team == team:
            goals_conceded.append(h.away_score)
        else:
            goals_conceded.append(h.home_score)

    avg_conceded = float(np.mean(goals_conceded)) if goals_conceded else 1.0
    discipline_proxy = 1.0 + (avg_conceded * 1.2)
    return float(np.clip(discipline_proxy, 0.5, 4.5))


# ---------------------------------------------------------------------------
# Tournament Weight Helper
# ---------------------------------------------------------------------------


def _get_tournament_weight(tournament: str) -> float:
    """Returns the importance weight for a given tournament string."""
    for key, weight in TOURNAMENT_WEIGHTS.items():
        if key.lower() in tournament.lower():
            return weight
    return 1.0


# ---------------------------------------------------------------------------
# Core Feature Assembly
# ---------------------------------------------------------------------------


def _build_match_features(
    row: pd.Series,
    team_hist: Dict[str, List[MatchRecord]],
    match_date: Optional[pd.Timestamp] = None,
) -> Dict:
    """
    Computes the full feature vector for a single historical training match.
    """
    home = row["home_team"]
    away = row["away_team"]
    date = match_date if match_date is not None else pd.Timestamp(row["date"])

    home_elo = float(row.get("home_elo", 1500.0))
    away_elo = float(row.get("away_elo", 1500.0))

    home_attack, home_defense = _get_rolling_rates(
        team_hist.get(home, []), home, date
    )
    away_attack, away_defense = _get_rolling_rates(
        team_hist.get(away, []), away, date
    )

    home_form = get_team_form(team_hist, home, date)
    away_form = get_team_form(team_hist, away, date)

    h2h_win_rate, h2h_goal_diff = get_h2h_features(team_hist, home, away, date)

    home_disc = compute_dynamic_discipline(team_hist, home, date)
    away_disc = compute_dynamic_discipline(team_hist, away, date)

    is_host = int(
        home in HOST_NATIONS and not bool(row.get("neutral", True))
    )

    tournament = row.get("tournament", "Friendly")
    t_weight = _get_tournament_weight(str(tournament))

    return {
        "elo_diff": home_elo - away_elo,
        "home_elo": home_elo,
        "away_elo": away_elo,
        "home_attack": home_attack,
        "home_defense": home_defense,
        "away_attack": away_attack,
        "away_defense": away_defense,
        "tournament_weight": t_weight,
        "is_host": is_host,
        "home_recent_form": home_form,
        "away_recent_form": away_form,
        "h2h_win_rate": h2h_win_rate,
        "h2h_goal_diff": h2h_goal_diff,
        "home_discipline": home_disc,
        "away_discipline": away_disc,
    }


def build_feature_matrix(
    df_matches: pd.DataFrame,
    team_hist: Dict[str, List[MatchRecord]],
) -> pd.DataFrame:
    """
    Constructs the full training feature matrix from the historical match DataFrame.

    Each row is a match; features capture the state of both teams at match time.
    Returns a DataFrame with columns = FEATURE_COLS plus target columns:
        home_goals, away_goals, home_yellow, away_yellow,
        home_red, away_red, home_corners, away_corners

    Note: yellow/red/corner targets are synthetic proxies (see spec §Feature Engineering).
    """
    logger.info(f"Building feature matrix for {len(df_matches):,} matches...")
    feature_rows = []

    for idx, row in df_matches.iterrows():
        feats = _build_match_features(row, team_hist)

        # Primary targets
        feats["home_goals"] = row["home_score"]
        feats["away_goals"] = row["away_score"]

        # Carry date for recency weighting in model training
        feats["date"] = row["date"]

        # Synthetic yellow card targets (Improvement #4 replaces static lookup)
        feats["home_yellow"] = feats["home_discipline"]
        feats["away_yellow"] = feats["away_discipline"]

        # Synthetic red card targets: binary (1 if discipline proxy > 3.0)
        feats["home_red"] = int(feats["home_discipline"] > 3.0)
        feats["away_red"] = int(feats["away_discipline"] > 3.0)

        # Synthetic corner targets: pressure-based Poisson draw
        home_pressure = feats["home_attack"] + (1.0 - min(feats["away_defense"], 1.0))
        away_pressure = feats["away_attack"] + (1.0 - min(feats["home_defense"], 1.0))
        feats["home_corners"] = float(
            np.random.poisson(max(home_pressure * 3.0, 1.0))
        )
        feats["away_corners"] = float(
            np.random.poisson(max(away_pressure * 3.0, 1.0))
        )

        feature_rows.append(feats)

        if (idx + 1) % 5000 == 0:
            logger.info(f"  Processed {idx + 1:,} / {len(df_matches):,} matches...")

    df_features = pd.DataFrame(feature_rows)

    # Guard against NaNs before returning
    nan_cols = df_features[FEATURE_COLS].columns[df_features[FEATURE_COLS].isna().any()]
    if len(nan_cols) > 0:
        logger.warning(f"NaN found in features {list(nan_cols)} — filling with column medians.")
        df_features[nan_cols] = df_features[nan_cols].fillna(df_features[nan_cols].median())

    logger.info(f"Feature matrix built: shape {df_features.shape}")
    return df_features


def build_prediction_row(
    home_team: str,
    away_team: str,
    team_hist: Dict[str, List[MatchRecord]],
    elo_dict: Dict[str, float],
    match_date: pd.Timestamp,
    is_neutral: bool = True,
    tournament: str = "FIFA World Cup",
) -> pd.DataFrame:
    """
    Constructs a single-row feature DataFrame for a future match prediction.

    Used during tournament simulation to get model inputs for each simulated match.
    """
    home_elo = elo_dict.get(home_team, 1500.0)
    away_elo = elo_dict.get(away_team, 1500.0)

    mock_row = pd.Series(
        {
            "home_team": home_team,
            "away_team": away_team,
            "date": match_date,
            "home_elo": home_elo,
            "away_elo": away_elo,
            "tournament": tournament,
            "neutral": is_neutral,
        }
    )

    feats = _build_match_features(mock_row, team_hist, match_date)
    return pd.DataFrame([feats])[FEATURE_COLS]
