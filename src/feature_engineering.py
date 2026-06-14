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
  build_team_history_dfs(team_hist) -> Dict[str, pd.DataFrame]
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

# Opponent-strength weighting for form and rolling rates (baseline = average Elo)
ELO_BASELINE = 1500.0
OPPONENT_WEIGHT_MIN = 0.5
OPPONENT_WEIGHT_MAX = 2.0


def _attack_adjustment_weights(opponent_elos: np.ndarray) -> np.ndarray:
    """Higher opponent Elo → scoring counts more toward attack rate."""
    raw = np.asarray(opponent_elos, dtype=float) / ELO_BASELINE
    return np.clip(raw, OPPONENT_WEIGHT_MIN, OPPONENT_WEIGHT_MAX)


def _defense_adjustment_weights(opponent_elos: np.ndarray) -> np.ndarray:
    """Higher opponent Elo → conceding counts less toward defence penalty."""
    raw = ELO_BASELINE / np.asarray(opponent_elos, dtype=float)
    return np.clip(raw, OPPONENT_WEIGHT_MIN, OPPONENT_WEIGHT_MAX)


def _form_adjustment_weights(opponent_elos: np.ndarray) -> np.ndarray:
    """Higher opponent Elo → result points count more toward form index."""
    return _attack_adjustment_weights(opponent_elos)


def _weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    """Weighted average; falls back to plain mean when weights sum to zero."""
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    total = float(w.sum())
    if total <= 0:
        return float(np.mean(v))
    return float(np.sum(v * w) / total)


def _quality_adjusted_form(points: np.ndarray, opponent_elos: np.ndarray) -> float:
    """
    Form index in [0, 1]: weighted points / weighted max points (3 per game).
    All-neutral opponents (1500 Elo) reduces to mean(points) / 3.
    """
    weights = _form_adjustment_weights(opponent_elos)
    pts = np.asarray(points, dtype=float)
    max_weighted = float(np.sum(3.0 * weights))
    if max_weighted <= 0:
        return 0.5
    return float(np.clip(np.sum(pts * weights) / max_weighted, 0.0, 1.0))


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
# Team History DataFrames (vectorized lookup backbone)
# ---------------------------------------------------------------------------


def build_team_history_dfs(
    team_hist: Dict[str, List[MatchRecord]],
) -> Dict[str, pd.DataFrame]:
    """
    Converts per-team MatchRecord lists into sorted DataFrames for fast slicing.

    Each row stores goals/points from that team's perspective.
    """
    dfs: Dict[str, pd.DataFrame] = {}
    for team, records in team_hist.items():
        if not records:
            continue
        rows = []
        for h in records:
            is_home = h.home_team == team
            if is_home:
                goals_scored, goals_conceded = h.home_score, h.away_score
            else:
                goals_scored, goals_conceded = h.away_score, h.home_score
            if goals_scored > goals_conceded:
                points = 3
            elif goals_scored == goals_conceded:
                points = 1
            else:
                points = 0
            opponent_elo = h.away_elo if is_home else h.home_elo
            rows.append(
                {
                    "date": h.date,
                    "opponent": h.away_team if is_home else h.home_team,
                    "opponent_elo": opponent_elo,
                    "home_team": h.home_team,
                    "away_team": h.away_team,
                    "home_score": h.home_score,
                    "away_score": h.away_score,
                    "goals_scored": goals_scored,
                    "goals_conceded": goals_conceded,
                    "points": points,
                    "was_home": is_home,
                }
            )
        dfs[team] = (
            pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
        )
    return dfs


def _slice_team_history_df(
    team_df: pd.DataFrame,
    current_date: pd.Timestamp,
    window: int,
) -> Optional[pd.DataFrame]:
    """Returns up to `window` rows strictly before current_date."""
    if team_df.empty:
        return None
    idx = int(team_df["date"].searchsorted(current_date, side="left"))
    if idx == 0:
        return None
    return team_df.iloc[max(0, idx - window) : idx]


def _rolling_rates_from_scored_conceded(
    scored: np.ndarray,
    conceded: np.ndarray,
    opponent_elos: Optional[np.ndarray] = None,
) -> Tuple[float, float]:
    """
    Shared rolling-rate logic for list and DataFrame backends.

    When opponent_elos is provided, goals scored are weighted by opponent Elo
    (stronger opponent → higher attack credit). Goals conceded are weighted
    inversely (conceding to stronger opponents is less penalizing).
    """
    n = len(scored)
    if n == 0:
        return 1.0, 1.0

    if opponent_elos is not None and len(opponent_elos) == n:
        attack_w = _attack_adjustment_weights(opponent_elos)
        defence_w = _defense_adjustment_weights(opponent_elos)
    else:
        attack_w = np.ones(n)
        defence_w = np.ones(n)

    if n <= 5:
        blend = n / 5.0
        attack = blend * _weighted_mean(scored, attack_w) + (1 - blend) * 1.0
        defence_conceded = (
            blend * _weighted_mean(conceded, defence_w) + (1 - blend) * 1.0
        )
    else:
        attack = (
            0.70 * _weighted_mean(scored[-5:], attack_w[-5:])
            + 0.30 * _weighted_mean(scored[:-5], attack_w[:-5])
        )
        defence_conceded = (
            0.70 * _weighted_mean(conceded[-5:], defence_w[-5:])
            + 0.30 * _weighted_mean(conceded[:-5], defence_w[:-5])
        )

    defense_rate = 1.0 / max(float(defence_conceded), 0.1)
    return float(attack), float(defense_rate)


def get_team_rolling_profile(
    team_df: Optional[pd.DataFrame],
    current_date: pd.Timestamp,
    window: int = 10,
) -> Dict[str, float | int]:
    """Raw rolling totals used for Bayesian-smoothed attack/defense awards."""
    empty: Dict[str, float | int] = {
        "goals_scored": 0,
        "goals_conceded": 0,
        "match_count": 0,
        "avg_opponent_elo": 1500.0,
        "last5_goals_scored": 0,
    }
    if team_df is None or team_df.empty:
        return empty

    recent = _slice_team_history_df(team_df, current_date, window)
    if recent is None or recent.empty:
        return empty

    last_five = recent.tail(5)
    return {
        "goals_scored": int(recent["goals_scored"].sum()),
        "goals_conceded": int(recent["goals_conceded"].sum()),
        "match_count": int(len(recent)),
        "avg_opponent_elo": float(recent["opponent_elo"].mean()),
        "last5_goals_scored": int(last_five["goals_scored"].sum()),
    }


def compute_global_rolling_averages(
    team_dfs: Dict[str, pd.DataFrame],
    teams: List[str],
    current_date: pd.Timestamp,
    window: int = 10,
) -> Tuple[float, float]:
    """Pool per-match goals/conceded across teams to estimate global priors."""
    from src.config import BAYESIAN_DEFAULT_AVG_CONCEDED, BAYESIAN_DEFAULT_AVG_GOALS

    scored: List[float] = []
    conceded: List[float] = []
    for team in teams:
        team_df = team_dfs.get(team)
        if team_df is None:
            continue
        recent = _slice_team_history_df(team_df, current_date, window)
        if recent is None or recent.empty:
            continue
        scored.extend(recent["goals_scored"].to_numpy(dtype=float))
        conceded.extend(recent["goals_conceded"].to_numpy(dtype=float))

    avg_goals = float(np.mean(scored)) if scored else BAYESIAN_DEFAULT_AVG_GOALS
    avg_conceded = float(np.mean(conceded)) if conceded else BAYESIAN_DEFAULT_AVG_CONCEDED
    return avg_goals, avg_conceded


def bayesian_smoothed_rate(
    total: float,
    games: int,
    global_avg: float,
    weight: int,
) -> float:
    if games <= 0:
        return float(global_avg)
    return (total + (global_avg * weight)) / (games + weight)


def bayesian_smoothed_raw_rate(
    raw_rate: float,
    games: int,
    global_avg: float,
    weight: int,
) -> float:
    if games <= 0:
        return float(global_avg)
    return (raw_rate * games + (global_avg * weight)) / (games + weight)


def elo_adjusted_attack_score(
    smoothed_attack: float,
    team_elo: float,
    mean_elo: float,
) -> float:
    if mean_elo <= 0:
        return smoothed_attack
    return smoothed_attack * (team_elo / mean_elo)


def elo_adjusted_fortress_score(
    smoothed_conceded: float,
    team_elo: float,
    mean_elo: float,
) -> float:
    if team_elo <= 0 or mean_elo <= 0:
        return smoothed_conceded
    return smoothed_conceded * (mean_elo / team_elo)


# ---------------------------------------------------------------------------
# Rolling Attack / Defence Rates
# ---------------------------------------------------------------------------


def _get_rolling_rates_from_df(
    team_df: pd.DataFrame,
    current_date: pd.Timestamp,
    window: int = 10,
) -> Tuple[float, float]:
    """Vectorized rolling attack/defence rates using a per-team DataFrame."""
    recent = _slice_team_history_df(team_df, current_date, window)
    if recent is None or recent.empty:
        return 1.0, 1.0
    return _rolling_rates_from_scored_conceded(
        recent["goals_scored"].to_numpy(),
        recent["goals_conceded"].to_numpy(),
        recent["opponent_elo"].to_numpy(),
    )


def _get_rolling_rates(
    history: List[MatchRecord],
    team: str,
    current_date: pd.Timestamp,
    window: int = 10,
    team_df: Optional[pd.DataFrame] = None,
) -> Tuple[float, float]:
    """
    Computes weighted rolling attack and defence rates for a team.

    Returns (attack_rate, defense_rate) where:
      - attack_rate  = avg goals scored
      - defense_rate = 1 / (avg goals conceded + ε)  [higher = stronger defense]

    Scheme from spec:
      - ≤5 games:  linear interpolation with neutral rate 1.0
      - 6–10 games: last 5 weighted 70%, prior 5 weighted 30%
      - Goals scored/conceded weighted by opponent Elo strength
    """
    if team_df is not None:
        return _get_rolling_rates_from_df(team_df, current_date, window)

    past = [h for h in history if h.date < current_date]
    if not past:
        return 1.0, 1.0

    recent = past[-window:]
    scored = np.empty(len(recent), dtype=float)
    conceded = np.empty(len(recent), dtype=float)
    opponent_elos = np.empty(len(recent), dtype=float)
    for i, h in enumerate(recent):
        if h.home_team == team:
            scored[i] = h.home_score
            conceded[i] = h.away_score
            opponent_elos[i] = h.away_elo
        else:
            scored[i] = h.away_score
            conceded[i] = h.home_score
            opponent_elos[i] = h.home_elo

    return _rolling_rates_from_scored_conceded(scored, conceded, opponent_elos)


# ---------------------------------------------------------------------------
# Improvement #2 — Rolling Form (Streak) Feature
# ---------------------------------------------------------------------------


def _get_team_form_from_df(
    team_df: pd.DataFrame,
    current_date: pd.Timestamp,
    window: int = 5,
) -> float:
    """Vectorized form index from a per-team DataFrame."""
    recent = _slice_team_history_df(team_df, current_date, window)
    if recent is None or recent.empty:
        return 0.5
    return _quality_adjusted_form(
        recent["points"].to_numpy(),
        recent["opponent_elo"].to_numpy(),
    )


def get_team_form(
    team_hist: Dict[str, List[MatchRecord]],
    team: str,
    current_date: pd.Timestamp,
    window: int = 5,
    team_dfs: Optional[Dict[str, pd.DataFrame]] = None,
) -> float:
    """
    Computes a form index based on points earned in the team's last N matches,
    weighted by opponent Elo (wins vs stronger sides count more).

    Returns a value in [0.0, 1.0]:
      - 1.0 = maximum form (all wins in last N games vs average opposition)
      - 0.0 = rock-bottom form (all losses)
      - Neutral default: 0.5 (no history)
    """
    if team_dfs is not None:
        team_df = team_dfs.get(team)
        if team_df is None:
            return 0.5
        return _get_team_form_from_df(team_df, current_date, window)

    history = team_hist.get(team, [])
    history = [h for h in history if h.date < current_date]

    if not history:
        return 0.5

    recent = history[-window:]
    points = np.empty(len(recent), dtype=float)
    opponent_elos = np.empty(len(recent), dtype=float)
    for i, h in enumerate(recent):
        if h.home_team == team:
            opponent_elos[i] = h.away_elo
            if h.home_score > h.away_score:
                points[i] = 3
            elif h.home_score == h.away_score:
                points[i] = 1
            else:
                points[i] = 0
        else:
            opponent_elos[i] = h.home_elo
            if h.away_score > h.home_score:
                points[i] = 3
            elif h.away_score == h.home_score:
                points[i] = 1
            else:
                points[i] = 0

    return _quality_adjusted_form(points, opponent_elos) if len(recent) else 0.5


# ---------------------------------------------------------------------------
# Improvement #3 — Head-to-Head (H2H) Features
# ---------------------------------------------------------------------------


def _get_h2h_features_from_df(
    team_a_df: pd.DataFrame,
    team_a: str,
    team_b: str,
    current_date: pd.Timestamp,
    max_lookback_years: float = 15.0,
) -> Tuple[float, float]:
    """Vectorized H2H stats from team_a's perspective."""
    current_dt = pd.Timestamp(current_date)
    cutoff = current_dt - pd.Timedelta(days=max_lookback_years * 365.25)
    mask = (
        (team_a_df["date"] >= cutoff)
        & (team_a_df["date"] < current_dt)
        & (team_a_df["opponent"] == team_b)
    )
    h2h = team_a_df.loc[mask]
    if h2h.empty:
        return 0.5, 0.0

    is_home = h2h["home_team"].to_numpy() == team_a
    goals_a = np.where(
        is_home, h2h["home_score"].to_numpy(), h2h["away_score"].to_numpy()
    )
    goals_b = np.where(
        is_home, h2h["away_score"].to_numpy(), h2h["home_score"].to_numpy()
    )
    goal_diffs = goals_a - goals_b
    wins = float(np.sum(goal_diffs > 0) + 0.5 * np.sum(goal_diffs == 0))
    win_rate = wins / len(h2h)
    return float(win_rate), float(np.mean(goal_diffs))


def get_h2h_features(
    team_hist: Dict[str, List[MatchRecord]],
    team_a: str,
    team_b: str,
    current_date: pd.Timestamp,
    max_lookback_years: float = 15.0,
    team_dfs: Optional[Dict[str, pd.DataFrame]] = None,
) -> Tuple[float, float]:
    """
    Retrieves historical H2H stats between team_a (home) and team_b (away).

    Returns
    -------
    (win_rate, avg_goal_diff) from team_a's perspective.
    Neutral defaults: (0.5, 0.0)
    """
    if team_dfs is not None:
        team_a_df = team_dfs.get(team_a)
        if team_a_df is None or team_a_df.empty:
            return 0.5, 0.0
        return _get_h2h_features_from_df(
            team_a_df, team_a, team_b, current_date, max_lookback_years
        )

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


def _compute_dynamic_discipline_from_df(
    team_df: pd.DataFrame,
    current_date: pd.Timestamp,
    window: int = 15,
) -> float:
    """Vectorized discipline proxy from a per-team DataFrame."""
    recent = _slice_team_history_df(team_df, current_date, window)
    if recent is None or recent.empty:
        return 2.0
    avg_conceded = float(np.mean(recent["goals_conceded"].to_numpy()))
    discipline_proxy = 1.0 + (avg_conceded * 1.2)
    return float(np.clip(discipline_proxy, 0.5, 4.5))


def compute_dynamic_discipline(
    team_hist: Dict[str, List[MatchRecord]],
    team: str,
    current_date: pd.Timestamp,
    window: int = 15,
    team_dfs: Optional[Dict[str, pd.DataFrame]] = None,
) -> float:
    """
    Computes a dynamic discipline rate proxy (expected yellow cards per game).

    Formula: discipline_proxy = 1.0 + (avg_conceded * 1.2), clipped to [0.5, 4.5]
    Baseline default: 2.0
    """
    if team_dfs is not None:
        team_df = team_dfs.get(team)
        if team_df is None:
            return 2.0
        return _compute_dynamic_discipline_from_df(team_df, current_date, window)

    history = team_hist.get(team, [])
    history = [h for h in history if h.date < current_date]

    if not history:
        return 2.0

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
    team_dfs: Optional[Dict[str, pd.DataFrame]] = None,
) -> Dict:
    """
    Computes the full feature vector for a single historical training match.
    """
    home = row["home_team"]
    away = row["away_team"]
    date = match_date if match_date is not None else pd.Timestamp(row["date"])

    home_elo = float(row.get("home_elo", 1500.0))
    away_elo = float(row.get("away_elo", 1500.0))

    home_df = team_dfs.get(home) if team_dfs else None
    away_df = team_dfs.get(away) if team_dfs else None

    home_attack, home_defense = _get_rolling_rates(
        team_hist.get(home, []), home, date, team_df=home_df
    )
    away_attack, away_defense = _get_rolling_rates(
        team_hist.get(away, []), away, date, team_df=away_df
    )

    home_form = get_team_form(team_hist, home, date, team_dfs=team_dfs)
    away_form = get_team_form(team_hist, away, date, team_dfs=team_dfs)

    h2h_win_rate, h2h_goal_diff = get_h2h_features(
        team_hist, home, away, date, team_dfs=team_dfs
    )

    home_disc = compute_dynamic_discipline(team_hist, home, date, team_dfs=team_dfs)
    away_disc = compute_dynamic_discipline(team_hist, away, date, team_dfs=team_dfs)

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


def _append_training_targets(feats: Dict, row: pd.Series) -> Dict:
    """Adds target columns and synthetic card/corner proxies for training."""
    feats["home_goals"] = row["home_score"]
    feats["away_goals"] = row["away_score"]
    feats["date"] = row["date"]
    feats["home_yellow"] = feats["home_discipline"]
    feats["away_yellow"] = feats["away_discipline"]
    feats["home_red"] = int(feats["home_discipline"] > 3.0)
    feats["away_red"] = int(feats["away_discipline"] > 3.0)

    home_pressure = feats["home_attack"] + (1.0 - min(feats["away_defense"], 1.0))
    away_pressure = feats["away_attack"] + (1.0 - min(feats["home_defense"], 1.0))
    # Deterministic corner proxy (stable across retrains; avoids noisy Poisson labels)
    feats["home_corners"] = float(max(round(home_pressure * 3.0), 1.0))
    feats["away_corners"] = float(max(round(away_pressure * 3.0), 1.0))
    return feats


def build_feature_matrix(
    df_matches: pd.DataFrame,
    team_hist: Dict[str, List[MatchRecord]],
) -> pd.DataFrame:
    """
    Constructs the full training feature matrix from the historical match DataFrame.

    Each row is a match; features capture the state of both teams at match time.
    Returns a DataFrame with columns = FEATURE_COLS plus target columns.
    """
    logger.info(f"Building feature matrix for {len(df_matches):,} matches...")
    team_dfs = build_team_history_dfs(team_hist)
    feature_rows = []

    for i, row in enumerate(df_matches.itertuples(index=False), start=1):
        row_series = pd.Series(row._asdict())
        feats = _build_match_features(row_series, team_hist, team_dfs=team_dfs)
        feats = _append_training_targets(feats, row_series)
        feature_rows.append(feats)

        if i % 5000 == 0:
            logger.info(f"  Processed {i:,} / {len(df_matches):,} matches...")

    df_features = pd.DataFrame(feature_rows)

    nan_cols = df_features[FEATURE_COLS].columns[df_features[FEATURE_COLS].isna().any()]
    if len(nan_cols) > 0:
        logger.warning(
            f"NaN found in features {list(nan_cols)} — filling with column medians."
        )
        df_features[nan_cols] = df_features[nan_cols].fillna(
            df_features[nan_cols].median()
        )

    logger.info(f"Feature matrix built: shape {df_features.shape}")
    return df_features


def load_or_build_feature_matrix(
    df_matches: pd.DataFrame,
    team_hist: Dict[str, List[MatchRecord]],
    data_dir: str | Path | None = None,
    force_rebuild: bool = False,
) -> pd.DataFrame:
    """
    Build feature matrix or load from disk cache when source data unchanged.
    """
    from pathlib import Path as _Path

    from src.cache_utils import (
        compute_data_fingerprint,
        feature_matrix_cache_path,
        load_cached_feature_matrix,
        save_feature_matrix_cache,
    )

    cache_path = None
    if data_dir is not None and not force_rebuild:
        data_path = _Path(data_dir)
        fingerprint = compute_data_fingerprint(data_path)
        cache_path = feature_matrix_cache_path(data_path, fingerprint)
        cached = load_cached_feature_matrix(cache_path)
        if cached is not None:
            return cached

    df_features = build_feature_matrix(df_matches, team_hist)

    if cache_path is not None:
        save_feature_matrix_cache(df_features, cache_path)

    return df_features


def build_prediction_row(
    home_team: str,
    away_team: str,
    team_hist: Dict[str, List[MatchRecord]],
    elo_dict: Dict[str, float],
    match_date: pd.Timestamp,
    is_neutral: bool = True,
    tournament: str = "FIFA World Cup",
    team_dfs: Optional[Dict[str, pd.DataFrame]] = None,
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

    feats = _build_match_features(
        mock_row, team_hist, match_date, team_dfs=team_dfs
    )
    return pd.DataFrame([feats])[FEATURE_COLS]
