"""
src/simulations.py
==================
Match-level simulation and Monte Carlo tournament engine.

Pipeline:
  1. simulate_match()           — draws goals/cards/corners from model lambdas
  2. simulate_extra_time()      — 0.8-goal extra time period
  3. simulate_penalties()       — Elo-calibrated shootout (Improvement #5)
  4. simulate_group_stage()     — full group stage with tiebreakers
  5. simulate_knockout_round()  — single-elimination match simulation
  6. run_monte_carlo()          — N iterations → aggregated prediction bundle

Public API:
  run_monte_carlo(
      team_hist, elo_df, models,
      n_simulations=10_000
  ) -> Dict[str, Any]
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.feature_engineering import build_prediction_row
from src.config import (
    FEATURE_COLS,
    TOURNAMENT_DATE,
    EXTRA_TIME_GOALS_EXPECTED,
    PENALTY_ELO_SCALE,
    PENALTY_PROB_MIN,
    PENALTY_PROB_MAX,
)
from src.helpers import (
    WC2026_GROUPS,
    build_knockout_bracket,
    get_group_fixtures,
    resolve_group_standings,
)
from src.models import ModelBundle, PredictionBundle, predict_lambdas

logger = logging.getLogger(__name__)


# Type alias for feature cache
FeatureCache = Dict[Tuple[str, str], "pd.DataFrame"]


# ---------------------------------------------------------------------------
# Feature Cache — Pre-compute all WC matchup features once
# ---------------------------------------------------------------------------


def build_feature_cache(
    team_hist: Dict,
    elo_dict: Dict[str, float],
) -> "FeatureCache":
    """
    Pre-computes build_prediction_row() for every ordered pair of WC teams.

    This is called once before the Monte Carlo loop. During simulation,
    features are looked up in O(1) instead of being recomputed for every
    match in every iteration.

    Returns
    -------
    dict[(home_team, away_team) -> feature DataFrame]
    """
    all_teams = [team for teams in WC2026_GROUPS.values() for team in teams]
    cache: Dict[Tuple[str, str], object] = {}
    total = len(all_teams) * (len(all_teams) - 1)
    logger.info(f"Pre-computing features for {total} WC team matchups...")

    for home_team in all_teams:
        for away_team in all_teams:
            if home_team == away_team:
                continue
            key = (home_team, away_team)
            cache[key] = build_prediction_row(
                home_team, away_team, team_hist, elo_dict, TOURNAMENT_DATE
            )

    logger.info(f"Feature cache built: {len(cache)} matchup vectors cached.")
    return cache


# ---------------------------------------------------------------------------
# Match-Level Simulation
# ---------------------------------------------------------------------------


def _draw_match_outcomes(pred: PredictionBundle) -> Dict[str, int]:
    """
    Draws match outcomes from model lambdas using appropriate distributions.

    - Goals:   Poisson(λ_goals)
    - Yellows: Poisson(λ_yellow)
    - Reds:    Bernoulli(p_red)
    - Corners: Poisson(λ_corners)
    """
    return {
        "home_goals": int(np.random.poisson(pred.home_goals_lambda)),
        "away_goals": int(np.random.poisson(pred.away_goals_lambda)),
        "home_yellow": int(np.random.poisson(max(pred.home_yellow_lambda, 0.01))),
        "away_yellow": int(np.random.poisson(max(pred.away_yellow_lambda, 0.01))),
        "home_red": int(np.random.random() < pred.home_red_prob),
        "away_red": int(np.random.random() < pred.away_red_prob),
        "home_corners": int(np.random.poisson(max(pred.home_corners_lambda, 1.0))),
        "away_corners": int(np.random.poisson(max(pred.away_corners_lambda, 1.0))),
    }


def simulate_extra_time(pred: PredictionBundle) -> Tuple[int, int]:
    """
    Simulates extra time for a drawn knockout match.

    Expected total goals = 0.8, split proportionally by team goal lambdas.

    Returns
    -------
    (extra_home_goals, extra_away_goals)
    """
    total_lambda = pred.home_goals_lambda + pred.away_goals_lambda
    if total_lambda < 1e-6:
        home_share = 0.5
    else:
        home_share = pred.home_goals_lambda / total_lambda

    home_et_lambda = EXTRA_TIME_GOALS_EXPECTED * home_share
    away_et_lambda = EXTRA_TIME_GOALS_EXPECTED * (1.0 - home_share)

    return (
        int(np.random.poisson(home_et_lambda)),
        int(np.random.poisson(away_et_lambda)),
    )


def simulate_penalties(home_team: str, away_team: str, pred: PredictionBundle) -> str:
    """
    Simulates a penalty shootout using Elo-calibrated probabilities.

    Improvement #5: Replaces flat 50/50 coin flip with sigmoid-scaled Elo difference.

    Formula: P(home wins) = sigmoid(elo_diff / 400), clipped to [0.35, 0.65]

    Returns
    -------
    Winning team name
    """
    elo_diff = pred.home_elo - pred.away_elo
    shootout_prob = 1.0 / (1.0 + np.exp(-elo_diff / PENALTY_ELO_SCALE))
    shootout_prob = float(np.clip(shootout_prob, PENALTY_PROB_MIN, PENALTY_PROB_MAX))

    return home_team if np.random.random() < shootout_prob else away_team


def simulate_match(
    home_team: str,
    away_team: str,
    team_hist: Dict,
    elo_dict: Dict[str, float],
    models: ModelBundle,
    knockout: bool = False,
    feature_cache: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Simulates a single match end-to-end.

    For knockout matches:
      - If drawn at 90 min -> simulate extra time
      - If still drawn -> simulate penalty shootout (Elo-calibrated)

    Parameters
    ----------
    feature_cache : optional pre-computed feature cache from build_feature_cache().
                   If provided, features are looked up in O(1) instead of recomputed.

    Returns a result dict with:
      home_goals, away_goals, home_yellow, away_yellow,
      home_red, away_red, home_corners, away_corners, winner (knockout only)
    """
    if feature_cache is not None and (home_team, away_team) in feature_cache:
        feature_row = feature_cache[(home_team, away_team)]
    else:
        feature_row = build_prediction_row(
            home_team, away_team, team_hist, elo_dict, TOURNAMENT_DATE
        )
    pred = predict_lambdas(models, feature_row)

    result = _draw_match_outcomes(pred)
    result["home_team"] = home_team
    result["away_team"] = away_team

    if knockout:
        hg, ag = result["home_goals"], result["away_goals"]

        if hg == ag:
            # Extra time
            et_home, et_away = simulate_extra_time(pred)
            hg += et_home
            ag += et_away
            result["home_goals"] = hg
            result["away_goals"] = ag

        if hg == ag:
            # Penalty shootout
            result["winner"] = simulate_penalties(home_team, away_team, pred)
        elif hg > ag:
            result["winner"] = home_team
        else:
            result["winner"] = away_team

    return result


# ---------------------------------------------------------------------------
# Group Stage Simulation
# ---------------------------------------------------------------------------


def simulate_group_stage(
    team_hist: Dict,
    elo_dict: Dict[str, float],
    models: ModelBundle,
    feature_cache: Optional[Dict] = None,
) -> Tuple[Dict[str, pd.DataFrame], List[Dict]]:
    """
    Simulates all 48 group stage fixtures for one MC iteration.

    Returns
    -------
    group_standings : dict[group -> sorted DataFrame with rank column]
    all_results     : list of all raw match result dicts
    """
    fixtures = get_group_fixtures()
    all_results = []

    # Collect results per group
    group_results: Dict[str, List[Dict]] = defaultdict(list)

    for fixture in fixtures:
        result = simulate_match(
            home_team=fixture["home_team"],
            away_team=fixture["away_team"],
            team_hist=team_hist,
            elo_dict=elo_dict,
            models=models,
            knockout=False,
            feature_cache=feature_cache,
        )
        result["match_id"] = fixture["match_id"]
        result["stage"] = "Group"
        result["group"] = fixture["group"]
        all_results.append(result)
        group_results[fixture["group"]].append(result)

    # Resolve standings per group
    group_standings = {}
    for group, results in group_results.items():
        standings = resolve_group_standings(results)
        group_standings[group] = standings

    return group_standings, all_results


# ---------------------------------------------------------------------------
# Knockout Round Simulation
# ---------------------------------------------------------------------------


def simulate_knockout_round(
    matchups: List[Dict],
    team_hist: Dict,
    elo_dict: Dict[str, float],
    models: ModelBundle,
    stage_name: str,
    feature_cache: Optional[Dict] = None,
) -> Tuple[List[str], List[Dict]]:
    """
    Simulates a full knockout round (e.g., R32, R16, QF, SF, Final).

    Returns
    -------
    winners     : list of winning team names (in bracket order)
    round_results: list of match result dicts
    """
    winners = []
    round_results = []

    for match in matchups:
        result = simulate_match(
            home_team=match["home_team"],
            away_team=match["away_team"],
            team_hist=team_hist,
            elo_dict=elo_dict,
            models=models,
            knockout=True,
            feature_cache=feature_cache,
        )
        result["stage"] = stage_name
        result["match_id"] = match.get("match_id", -1)
        winners.append(result["winner"])
        round_results.append(result)

    return winners, round_results


def _pair_winners(winners: List[str], start_match_id: int, stage: str) -> List[Dict]:
    """Pairs consecutive winners into next-round matchups."""
    matchups = []
    for i in range(0, len(winners), 2):
        if i + 1 < len(winners):
            matchups.append(
                {
                    "match_id": start_match_id + i // 2,
                    "stage": stage,
                    "home_team": winners[i],
                    "away_team": winners[i + 1],
                    "neutral": True,
                }
            )
    return matchups


# ---------------------------------------------------------------------------
# Monte Carlo Engine
# ---------------------------------------------------------------------------


def run_monte_carlo(
    team_hist: Dict,
    elo_df: Dict[str, float],
    models: ModelBundle,
    n_simulations: int = 10_000,
) -> Dict[str, Any]:
    """
    Runs N Monte Carlo tournament simulations and aggregates results.

    Pre-computes feature vectors for all WC team matchups once before the
    simulation loop for O(1) feature lookup per match (major speedup).

    Aggregation per match:
      - Most common scoreline (mode of home_goals, away_goals)
      - Win/draw/loss probabilities
      - Tournament winner frequency

    Parameters
    ----------
    team_hist     : built by preprocessing.build_team_history()
    elo_df        : Elo ratings dict (team -> Elo)
    models        : trained ModelBundle
    n_simulations : number of MC iterations (default 10,000)

    Returns
    -------
    dict with keys:
      - 'match_results': dict[match_id -> aggregated stats]
      - 'champion_probs': dict[team -> P(winning WC)]
      - 'finalist_probs': dict[team -> P(reaching Final)]
    """
    logger.info(f"Starting Monte Carlo simulation: N = {n_simulations:,}")

    # Pre-build feature cache for all WC matchups (key optimization)
    feature_cache = build_feature_cache(team_hist, elo_df)

    # Accumulators
    match_home_goals: Dict[int, List[int]] = defaultdict(list)
    match_away_goals: Dict[int, List[int]] = defaultdict(list)
    match_home_wins: Dict[int, int] = defaultdict(int)
    match_draws: Dict[int, int] = defaultdict(int)
    match_away_wins: Dict[int, int] = defaultdict(int)
    match_metadata: Dict[int, Dict] = {}

    champion_counter: Counter = Counter()
    finalist_counter: Counter = Counter()
    semifinalist_counter: Counter = Counter()

    for iteration in range(n_simulations):
        if (iteration + 1) % 1000 == 0:
            logger.info(f"  Iteration {iteration + 1:,} / {n_simulations:,}")

        np.random.seed(iteration)  # Reproducible per-iteration seed

        # --- Group Stage ---
        group_standings, group_results = simulate_group_stage(
            team_hist, elo_df, models, feature_cache=feature_cache
        )

        for res in group_results:
            mid = res["match_id"]
            match_home_goals[mid].append(res["home_goals"])
            match_away_goals[mid].append(res["away_goals"])
            if res["home_goals"] > res["away_goals"]:
                match_home_wins[mid] += 1
            elif res["home_goals"] == res["away_goals"]:
                match_draws[mid] += 1
            else:
                match_away_wins[mid] += 1
            if mid not in match_metadata:
                match_metadata[mid] = {
                    "home_team": res["home_team"],
                    "away_team": res["away_team"],
                    "stage": res["stage"],
                }

        # --- Round of 32 ---
        r32_matchups = build_knockout_bracket(group_standings)
        r32_winners, r32_results = simulate_knockout_round(
            r32_matchups, team_hist, elo_df, models, "Round of 32", feature_cache=feature_cache
        )
        _accumulate_knockout(
            r32_results, match_home_goals, match_away_goals,
            match_home_wins, match_draws, match_away_wins, match_metadata
        )

        # --- Round of 16 ---
        r16_matchups = _pair_winners(r32_winners, start_match_id=65, stage="Round of 16")
        r16_winners, r16_results = simulate_knockout_round(
            r16_matchups, team_hist, elo_df, models, "Round of 16", feature_cache=feature_cache
        )
        _accumulate_knockout(
            r16_results, match_home_goals, match_away_goals,
            match_home_wins, match_draws, match_away_wins, match_metadata
        )

        # --- Quarter-Finals ---
        qf_matchups = _pair_winners(r16_winners, start_match_id=73, stage="Quarter-Final")
        qf_winners, qf_results = simulate_knockout_round(
            qf_matchups, team_hist, elo_df, models, "Quarter-Final", feature_cache=feature_cache
        )
        _accumulate_knockout(
            qf_results, match_home_goals, match_away_goals,
            match_home_wins, match_draws, match_away_wins, match_metadata
        )

        # --- Semi-Finals ---
        sf_matchups = _pair_winners(qf_winners, start_match_id=77, stage="Semi-Final")
        sf_winners, sf_results = simulate_knockout_round(
            sf_matchups, team_hist, elo_df, models, "Semi-Final", feature_cache=feature_cache
        )
        _accumulate_knockout(
            sf_results, match_home_goals, match_away_goals,
            match_home_wins, match_draws, match_away_wins, match_metadata
        )
        for team in sf_winners:
            finalist_counter[team] += 1
        for team in qf_winners:
            semifinalist_counter[team] += 1

        # --- Final ---
        if len(sf_winners) >= 2:
            final_matchup = [
                {"match_id": 79, "stage": "Final",
                 "home_team": sf_winners[0], "away_team": sf_winners[1], "neutral": True}
            ]
            final_winners, final_results = simulate_knockout_round(
                final_matchup, team_hist, elo_df, models, "Final", feature_cache=feature_cache
            )
            _accumulate_knockout(
                final_results, match_home_goals, match_away_goals,
                match_home_wins, match_draws, match_away_wins, match_metadata
            )
            if final_winners:
                champion_counter[final_winners[0]] += 1

    # --- Aggregate Results ---
    logger.info("Aggregating Monte Carlo results...")
    mc_results = {}
    for mid in sorted(match_home_goals.keys()):
        n = len(match_home_goals[mid])
        if n == 0:
            continue
        hw = match_home_wins[mid]
        dr = match_draws[mid]
        aw = match_away_wins[mid]
        mc_results[mid] = {
            **match_metadata.get(mid, {}),
            "most_common_home_goals": Counter(match_home_goals[mid]).most_common(1)[0][0],
            "most_common_away_goals": Counter(match_away_goals[mid]).most_common(1)[0][0],
            "home_win_prob": hw / n,
            "draw_prob": dr / n,
            "away_win_prob": aw / n,
            "n_simulations": n,
        }

    champion_probs = {t: c / n_simulations for t, c in champion_counter.most_common()}
    finalist_probs = {t: c / n_simulations for t, c in finalist_counter.most_common()}

    logger.info("Monte Carlo complete.")
    _log_champion_table(champion_probs)

    return {
        "match_results": mc_results,
        "champion_probs": champion_probs,
        "finalist_probs": finalist_probs,
    }


def _accumulate_knockout(
    results: List[Dict],
    home_goals: Dict,
    away_goals: Dict,
    home_wins: Dict,
    draws: Dict,
    away_wins: Dict,
    metadata: Dict,
) -> None:
    """Accumulates knockout round results into the MC counters."""
    for res in results:
        mid = res.get("match_id", -1)
        if mid < 0:
            return
        home_goals[mid].append(res["home_goals"])
        away_goals[mid].append(res["away_goals"])
        hg, ag = res["home_goals"], res["away_goals"]
        winner = res.get("winner")
        if winner == res["home_team"]:
            home_wins[mid] += 1
        elif winner == res["away_team"]:
            away_wins[mid] += 1
        else:
            if hg > ag:
                home_wins[mid] += 1
            elif hg == ag:
                draws[mid] += 1
            else:
                away_wins[mid] += 1
        if mid not in metadata:
            metadata[mid] = {
                "home_team": res["home_team"],
                "away_team": res["away_team"],
                "stage": res["stage"],
            }


def _log_champion_table(champion_probs: Dict[str, float]) -> None:
    """Logs the top-16 predicted WC winners."""
    logger.info("\n  [RESULTS] World Cup Win Probabilities (Top 16):")
    for i, (team, prob) in enumerate(
        sorted(champion_probs.items(), key=lambda x: -x[1])[:16]
    ):
        bar = "#" * int(prob * 40)
        logger.info(f"  {i+1:>2}. {team:<25} {prob:>6.1%}  {bar}")
