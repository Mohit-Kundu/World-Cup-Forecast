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

      n_simulations=N_SIMULATIONS_DEFAULT

  ) -> Dict[str, Any]

"""



from __future__ import annotations



import logging

from dataclasses import dataclass, field

from collections import Counter, defaultdict

from typing import Any, Dict, List, Optional, Tuple



import numpy as np

import pandas as pd



from src.feature_engineering import build_prediction_row, build_team_history_dfs

from src.config import (

    RANDOM_SEED,

    TOURNAMENT_DATE,

    EXTRA_TIME_GOALS_EXPECTED,

    PENALTY_ELO_SCALE,

    PENALTY_PROB_MIN,

    PENALTY_PROB_MAX,

    N_SIMULATIONS_DEFAULT,

    CONVERGENCE_BATCH_SIZE,

    CONVERGENCE_MAX_ITERATIONS,

    CONVERGENCE_TOL,

    CONVERGENCE_MIN_N,

    CONVERGENCE_STABLE_BATCHES,

    CONVERGENCE_TOP_K,

    WC2026_GROUPS as CONFIG_WC2026_GROUPS,

)

from src.helpers import (

    WC2026_GROUPS,

    build_knockout_bracket,

    build_predicted_final,

    build_predicted_group_standings,

    get_group_fixtures,

    resolve_group_standings,

)

from src.models import ModelBundle, PredictionBundle, predict_lambdas



logger = logging.getLogger(__name__)





# Type aliases for pre-computed caches

FeatureCache = Dict[Tuple[str, str], pd.DataFrame]

LambdaCache = Dict[Tuple[str, str], PredictionBundle]





# ---------------------------------------------------------------------------

# Feature & Lambda Caches — Pre-compute all WC matchup inputs once

# ---------------------------------------------------------------------------





def build_feature_cache(

    team_hist: Dict,

    elo_dict: Dict[str, float],

) -> FeatureCache:

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

    team_dfs = build_team_history_dfs(team_hist)

    cache: FeatureCache = {}

    total = len(all_teams) * (len(all_teams) - 1)

    logger.info(f"Pre-computing features for {total} WC team matchups...")



    for home_team in all_teams:

        for away_team in all_teams:

            if home_team == away_team:

                continue

            key = (home_team, away_team)

            cache[key] = build_prediction_row(

                home_team,

                away_team,

                team_hist,

                elo_dict,

                TOURNAMENT_DATE,

                team_dfs=team_dfs,

            )



    logger.info(f"Feature cache built: {len(cache)} matchup vectors cached.")

    return cache





def build_lambda_cache(

    feature_cache: FeatureCache,

    models: ModelBundle,

) -> LambdaCache:

    """

    Pre-computes predict_lambdas() for every cached WC matchup.



    Group-stage lambdas are fixed across Monte Carlo iterations, so this

    removes hundreds of thousands of redundant LightGBM inference calls.

    """

    logger.info(f"Pre-computing lambdas for {len(feature_cache)} WC matchups...")

    cache: LambdaCache = {}

    for key, feature_row in feature_cache.items():

        cache[key] = predict_lambdas(models, feature_row)

    logger.info(f"Lambda cache built: {len(cache)} prediction bundles cached.")

    return cache





def _lookup_pred(

    home_team: str,

    away_team: str,

    team_hist: Dict,

    elo_dict: Dict[str, float],

    models: ModelBundle,

    feature_cache: Optional[FeatureCache] = None,

    lambda_cache: Optional[LambdaCache] = None,

) -> PredictionBundle:

    """Resolves a PredictionBundle from cache or falls back to live inference."""

    key = (home_team, away_team)

    if lambda_cache is not None and key in lambda_cache:

        return lambda_cache[key]



    if feature_cache is not None and key in feature_cache:

        feature_row = feature_cache[key]

    else:

        feature_row = build_prediction_row(

            home_team, away_team, team_hist, elo_dict, TOURNAMENT_DATE

        )

    return predict_lambdas(models, feature_row)





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





def _draw_group_stage_batch(

    preds: List[PredictionBundle],

    n_simulations: int,

    seed: int = RANDOM_SEED,

) -> Dict[str, np.ndarray]:

    """

    Vectorized group-stage outcome draws for all fixtures × all simulations.



    Returns arrays of shape (n_simulations, n_fixtures) for each outcome stat.

    """

    n_fixtures = len(preds)

    home_goals_lam = np.array([p.home_goals_lambda for p in preds])

    away_goals_lam = np.array([p.away_goals_lambda for p in preds])

    home_yellow_lam = np.maximum(

        np.array([p.home_yellow_lambda for p in preds]), 0.01

    )

    away_yellow_lam = np.maximum(

        np.array([p.away_yellow_lambda for p in preds]), 0.01

    )

    home_red_prob = np.array([p.home_red_prob for p in preds])

    away_red_prob = np.array([p.away_red_prob for p in preds])

    home_corners_lam = np.maximum(

        np.array([p.home_corners_lambda for p in preds]), 1.0

    )

    away_corners_lam = np.maximum(

        np.array([p.away_corners_lambda for p in preds]), 1.0

    )



    rng = np.random.default_rng(seed)

    shape = (n_simulations, n_fixtures)



    return {

        "home_goals": rng.poisson(home_goals_lam, size=shape),

        "away_goals": rng.poisson(away_goals_lam, size=shape),

        "home_yellow": rng.poisson(home_yellow_lam, size=shape),

        "away_yellow": rng.poisson(away_yellow_lam, size=shape),

        "home_red": rng.random(shape) < home_red_prob,

        "away_red": rng.random(shape) < away_red_prob,

        "home_corners": rng.poisson(home_corners_lam, size=shape),

        "away_corners": rng.poisson(away_corners_lam, size=shape),

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





def _finalize_knockout_result(

    result: Dict[str, Any],

    home_team: str,

    away_team: str,

    pred: PredictionBundle,

) -> Dict[str, Any]:

    """Applies extra time and penalty logic to a knockout match result."""

    hg, ag = result["home_goals"], result["away_goals"]



    if hg == ag:

        et_home, et_away = simulate_extra_time(pred)

        hg += et_home

        ag += et_away

        result["home_goals"] = hg

        result["away_goals"] = ag



    if hg == ag:

        result["winner"] = simulate_penalties(home_team, away_team, pred)

    elif hg > ag:

        result["winner"] = home_team

    else:

        result["winner"] = away_team



    return result





def simulate_match(

    home_team: str,

    away_team: str,

    team_hist: Dict,

    elo_dict: Dict[str, float],

    models: ModelBundle,

    knockout: bool = False,

    feature_cache: Optional[FeatureCache] = None,

    lambda_cache: Optional[LambdaCache] = None,

) -> Dict[str, Any]:

    """

    Simulates a single match end-to-end.



    For knockout matches:

      - If drawn at 90 min -> simulate extra time

      - If still drawn -> simulate penalty shootout (Elo-calibrated)



    Parameters

    ----------

    feature_cache : optional pre-computed feature cache from build_feature_cache().

    lambda_cache  : optional pre-computed lambda cache from build_lambda_cache().



    Returns a result dict with:

      home_goals, away_goals, home_yellow, away_yellow,

      home_red, away_red, home_corners, away_corners, winner (knockout only)

    """

    pred = _lookup_pred(

        home_team, away_team, team_hist, elo_dict, models,

        feature_cache=feature_cache, lambda_cache=lambda_cache,

    )



    result = _draw_match_outcomes(pred)

    result["home_team"] = home_team

    result["away_team"] = away_team



    if knockout:

        result = _finalize_knockout_result(result, home_team, away_team, pred)



    return result





# ---------------------------------------------------------------------------

# Group Stage Simulation

# ---------------------------------------------------------------------------





def _group_standings_from_batch(

    draws: Dict[str, np.ndarray],

    sim_idx: int,

    fixtures: List[Dict],

    rng: Optional[np.random.Generator] = None,

) -> Tuple[Dict[str, pd.DataFrame], List[Dict]]:

    """Builds group standings and raw results for one simulation index."""

    group_results: Dict[str, List[Dict]] = defaultdict(list)

    all_results: List[Dict] = []



    for j, fixture in enumerate(fixtures):

        result = {

            "match_id": fixture["match_id"],

            "stage": "Group",

            "group": fixture["group"],

            "home_team": fixture["home_team"],

            "away_team": fixture["away_team"],

            "home_goals": int(draws["home_goals"][sim_idx, j]),

            "away_goals": int(draws["away_goals"][sim_idx, j]),

            "home_yellow": int(draws["home_yellow"][sim_idx, j]),

            "away_yellow": int(draws["away_yellow"][sim_idx, j]),

            "home_red": int(draws["home_red"][sim_idx, j]),

            "away_red": int(draws["away_red"][sim_idx, j]),

            "home_corners": int(draws["home_corners"][sim_idx, j]),

            "away_corners": int(draws["away_corners"][sim_idx, j]),

        }

        all_results.append(result)

        group_results[fixture["group"]].append(result)



    group_standings = {

        group: resolve_group_standings(results, rng=rng)

        for group, results in group_results.items()

    }

    return group_standings, all_results





def _extend_goal_store(store: Dict[int, np.ndarray], match_id: int, values: np.ndarray) -> None:

    """Append simulation goal counts using numpy concat (faster than Python lists)."""

    col = np.asarray(values, dtype=np.int32)

    if match_id in store:

        store[match_id] = np.concatenate([store[match_id], col])

    else:

        store[match_id] = col





def _accumulate_group_stage_batch(

    draws: Dict[str, np.ndarray],

    fixtures: List[Dict],

    match_home_goals: Dict[int, List[int]],

    match_away_goals: Dict[int, List[int]],

    match_home_wins: Dict[int, int],

    match_draws: Dict[int, int],

    match_away_wins: Dict[int, int],

    match_metadata: Dict[int, Dict],

) -> None:

    """Vectorized accumulation of group-stage results across all simulations."""

    hg = draws["home_goals"]

    ag = draws["away_goals"]



    for j, fixture in enumerate(fixtures):

        mid = fixture["match_id"]

        _extend_goal_store(match_home_goals, mid, hg[:, j])

        _extend_goal_store(match_away_goals, mid, ag[:, j])

        match_home_wins[mid] = int(np.sum(hg[:, j] > ag[:, j]))

        match_draws[mid] = int(np.sum(hg[:, j] == ag[:, j]))

        match_away_wins[mid] = int(np.sum(hg[:, j] < ag[:, j]))

        match_metadata[mid] = {

            "home_team": fixture["home_team"],

            "away_team": fixture["away_team"],

            "stage": "Group",

        }





def simulate_group_stage(

    team_hist: Dict,

    elo_dict: Dict[str, float],

    models: ModelBundle,

    feature_cache: Optional[FeatureCache] = None,

    lambda_cache: Optional[LambdaCache] = None,

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

            lambda_cache=lambda_cache,

        )

        result["match_id"] = fixture["match_id"]

        result["stage"] = "Group"

        result["group"] = fixture["group"]

        all_results.append(result)

        group_results[fixture["group"]].append(result)



    group_standings = {

        group: resolve_group_standings(results)

        for group, results in group_results.items()

    }

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

    feature_cache: Optional[FeatureCache] = None,

    lambda_cache: Optional[LambdaCache] = None,

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

            lambda_cache=lambda_cache,

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





@dataclass

class MonteCarloAccumulator:

    """Cumulative state for batched Monte Carlo tournament simulations."""



    match_home_goals: Dict[int, np.ndarray] = field(default_factory=dict)

    match_away_goals: Dict[int, np.ndarray] = field(default_factory=dict)

    match_home_wins: Dict[int, int] = field(default_factory=lambda: defaultdict(int))

    match_draws: Dict[int, int] = field(default_factory=lambda: defaultdict(int))

    match_away_wins: Dict[int, int] = field(default_factory=lambda: defaultdict(int))

    match_metadata: Dict[int, Dict] = field(default_factory=dict)

    champion_counter: Counter = field(default_factory=Counter)

    finalist_counter: Counter = field(default_factory=Counter)

    qualify_counter: Counter = field(default_factory=Counter)

    r32_counter: Counter = field(default_factory=Counter)

    r16_counter: Counter = field(default_factory=Counter)

    qf_counter: Counter = field(default_factory=Counter)

    sf_counter: Counter = field(default_factory=Counter)

    final_pairing_counter: Counter = field(default_factory=Counter)

    final_winner_by_pairing: Dict[Tuple[str, str], Counter] = field(

        default_factory=lambda: defaultdict(Counter)

    )



    @property

    def n_simulations(self) -> int:

        if not self.champion_counter:

            return 0

        return int(sum(self.champion_counter.values()))





def _all_wc_teams() -> List[str]:

    return [team for teams in CONFIG_WC2026_GROUPS.values() for team in teams]





def _append_group_stage_batch(

    draws: Dict[str, np.ndarray],

    fixtures: List[Dict],

    match_home_goals: Dict[int, List[int]],

    match_away_goals: Dict[int, List[int]],

    match_home_wins: Dict[int, int],

    match_draws: Dict[int, int],

    match_away_wins: Dict[int, int],

    match_metadata: Dict[int, Dict],

) -> None:

    """Appends vectorized group-stage results for one batch."""

    hg = draws["home_goals"]

    ag = draws["away_goals"]

    for j, fixture in enumerate(fixtures):

        mid = fixture["match_id"]

        _extend_goal_store(match_home_goals, mid, hg[:, j])

        _extend_goal_store(match_away_goals, mid, ag[:, j])

        match_home_wins[mid] += int(np.sum(hg[:, j] > ag[:, j]))

        match_draws[mid] += int(np.sum(hg[:, j] == ag[:, j]))

        match_away_wins[mid] += int(np.sum(hg[:, j] < ag[:, j]))

        if mid not in match_metadata:

            match_metadata[mid] = {

                "home_team": fixture["home_team"],

                "away_team": fixture["away_team"],

                "stage": "Group",

            }





def _run_knockout_loop_for_batch(

    acc: MonteCarloAccumulator,

    group_draws: Dict[str, np.ndarray],

    fixtures: List[Dict],

    batch_start: int,

    batch_size: int,

    team_hist: Dict,

    elo_df: Dict[str, float],

    models: ModelBundle,

    feature_cache: FeatureCache,

    lambda_cache: LambdaCache,

    log_progress: bool = True,

    progress_total: Optional[int] = None,

) -> None:

    """Runs knockout rounds for simulation indices in [batch_start, batch_start + batch_size)."""

    from src.knockout_engine import run_knockout_loop_parallel

    run_knockout_loop_parallel(

        acc,

        group_draws,

        fixtures,

        batch_start,

        batch_size,

        team_hist,

        elo_df,

        models,

        feature_cache,

        lambda_cache,

        log_progress=log_progress,

        progress_total=progress_total,

    )





def _run_monte_carlo_batch(

    acc: MonteCarloAccumulator,

    batch_start: int,

    batch_size: int,

    team_hist: Dict,

    elo_df: Dict[str, float],

    models: ModelBundle,

    feature_cache: FeatureCache,

    lambda_cache: LambdaCache,

    fixtures: List[Dict],

    group_preds: List[PredictionBundle],

    log_progress: bool = True,

    progress_total: Optional[int] = None,

) -> None:

    """Runs one batch of simulations and merges results into acc."""

    group_draws = _draw_group_stage_batch(

        group_preds, batch_size, seed=RANDOM_SEED + batch_start

    )

    _append_group_stage_batch(

        group_draws, fixtures,

        acc.match_home_goals, acc.match_away_goals,

        acc.match_home_wins, acc.match_draws, acc.match_away_wins, acc.match_metadata,

    )

    _run_knockout_loop_for_batch(

        acc, group_draws, fixtures, batch_start, batch_size,

        team_hist, elo_df, models, feature_cache, lambda_cache,

        log_progress=log_progress, progress_total=progress_total,

    )





def _champion_probs_dict(champion_counter: Counter, n_total: int) -> Dict[str, float]:

    if n_total <= 0:

        return {}

    return {team: count / n_total for team, count in champion_counter.items()}





def _finalize_monte_carlo_from_accumulator(

    acc: MonteCarloAccumulator,

    n_simulations: int,

) -> Dict[str, Any]:

    logger.info("Aggregating Monte Carlo results...")

    mc_results: Dict[int, Dict[str, Any]] = {}

    for mid in sorted(acc.match_home_goals.keys()):

        n = len(acc.match_home_goals[mid])

        if n == 0:

            continue

        hw = acc.match_home_wins[mid]

        dr = acc.match_draws[mid]

        aw = acc.match_away_wins[mid]

        mc_results[mid] = {

            **acc.match_metadata.get(mid, {}),

            "most_common_home_goals": Counter(acc.match_home_goals[mid]).most_common(1)[0][0],

            "most_common_away_goals": Counter(acc.match_away_goals[mid]).most_common(1)[0][0],

            "home_win_prob": hw / n,

            "draw_prob": dr / n,

            "away_win_prob": aw / n,

            "n_simulations": n,

        }



    champion_probs = _champion_probs_dict(acc.champion_counter, n_simulations)

    finalist_probs = {t: c / n_simulations for t, c in acc.finalist_counter.most_common()}

    qualify_probs = {t: c / n_simulations for t, c in acc.qualify_counter.most_common()}

    r32_probs = {t: c / n_simulations for t, c in acc.r32_counter.most_common()}

    r16_probs = {t: c / n_simulations for t, c in acc.r16_counter.most_common()}

    qf_probs = {t: c / n_simulations for t, c in acc.qf_counter.most_common()}

    sf_probs = {t: c / n_simulations for t, c in acc.sf_counter.most_common()}



    group_standings = build_predicted_group_standings(mc_results, qualify_probs)

    predicted_final = build_predicted_final(

        acc.final_pairing_counter, acc.final_winner_by_pairing, n_simulations

    )



    logger.info("Monte Carlo complete.")

    _log_champion_table(champion_probs)



    return {

        "match_results": mc_results,

        "champion_probs": champion_probs,

        "finalist_probs": finalist_probs,

        "qualify_probs": qualify_probs,

        "r32_probs": r32_probs,

        "r16_probs": r16_probs,

        "qf_probs": qf_probs,

        "sf_probs": sf_probs,

        "group_standings": group_standings,

        "predicted_final": predicted_final,

    }





def _top_k_teams_by_champion_count(champion_counter: Counter, top_k: int) -> List[str]:

    return [team for team, _ in champion_counter.most_common(top_k)]





def _checkpoint_snapshot(

    acc: MonteCarloAccumulator,

    n_total: int,

    prev_top_probs: Optional[Dict[str, float]],

    top_k: int = CONVERGENCE_TOP_K,

) -> Dict[str, Any]:

    champion_probs = _champion_probs_dict(acc.champion_counter, n_total)

    all_teams = _all_wc_teams()

    all_probs = np.array([champion_probs.get(team, 0.0) for team in all_teams])



    top_teams = _top_k_teams_by_champion_count(acc.champion_counter, top_k)

    top_probs = {team: champion_probs.get(team, 0.0) for team in top_teams}

    mean_top_k = float(np.mean(list(top_probs.values()))) if top_probs else 0.0



    max_delta = float("inf")

    if prev_top_probs is not None and top_probs:

        deltas = [abs(top_probs[team] - prev_top_probs.get(team, 0.0)) for team in top_probs]

        max_delta = float(max(deltas)) if deltas else float("inf")



    return {

        "n_simulations": n_total,

        "champion_probs": champion_probs,

        "top_teams": top_teams,

        "top_probs": top_probs,

        "mean_champion_prob_top_k": mean_top_k,

        "median_champion_prob_all": float(np.median(all_probs)),

        "p90_champion_prob_all": float(np.percentile(all_probs, 90)),

        "max_top_k_delta": max_delta,

    }





def run_monte_carlo_checkpoints(

    team_hist: Dict,

    elo_df: Dict[str, float],

    models: ModelBundle,

    batch_size: int = CONVERGENCE_BATCH_SIZE,

    max_iterations: int = CONVERGENCE_MAX_ITERATIONS,

    stop_on_convergence: bool = True,

    tol: float = CONVERGENCE_TOL,

    min_n: int = CONVERGENCE_MIN_N,

    stable_batches: int = CONVERGENCE_STABLE_BATCHES,

    top_k: int = CONVERGENCE_TOP_K,

) -> List[Dict[str, Any]]:

    """Run Monte Carlo in cumulative batches, recording convergence checkpoints."""

    logger.info(

        "Starting convergence sweep: batch=%s, max=%s",

        f"{batch_size:,}", f"{max_iterations:,}",

    )



    feature_cache = build_feature_cache(team_hist, elo_df)

    lambda_cache = build_lambda_cache(feature_cache, models)

    fixtures = get_group_fixtures()

    group_preds = [lambda_cache[(f["home_team"], f["away_team"])] for f in fixtures]



    acc = MonteCarloAccumulator()

    checkpoints: List[Dict[str, Any]] = []

    prev_top_probs: Optional[Dict[str, float]] = None

    n_total = 0

    stable_count = 0

    stopped_early = False



    while n_total < max_iterations:

        current_batch = min(batch_size, max_iterations - n_total)

        _run_monte_carlo_batch(

            acc, batch_start=n_total, batch_size=current_batch,

            team_hist=team_hist, elo_df=elo_df, models=models,

            feature_cache=feature_cache, lambda_cache=lambda_cache,

            fixtures=fixtures, group_preds=group_preds,

            log_progress=True, progress_total=max_iterations,

        )

        n_total += current_batch

        snapshot = _checkpoint_snapshot(acc, n_total, prev_top_probs, top_k=top_k)

        checkpoints.append(snapshot)



        if stop_on_convergence and n_total >= min_n:

            if snapshot["max_top_k_delta"] < tol:

                stable_count += 1

            else:

                stable_count = 0

            if stable_count >= stable_batches:

                logger.info(

                    "Convergence reached at N=%s (delta below %s for %s checkpoints)",

                    f"{n_total:,}", tol, stable_batches,

                )

                stopped_early = True

                break



        prev_top_probs = snapshot["top_probs"]



    if not stopped_early:

        logger.info("Convergence sweep finished at N=%s (max cap)", f"{n_total:,}")



    return checkpoints







def run_monte_carlo(

    team_hist: Dict,

    elo_df: Dict[str, float],

    models: ModelBundle,

    n_simulations: int = N_SIMULATIONS_DEFAULT,

) -> Dict[str, Any]:

    """

    Runs N Monte Carlo tournament simulations and aggregates results.



    Optimizations:

      - Feature + lambda caches for all WC matchups (computed once)

      - Vectorized group-stage draws across all N simulations

      - Vectorized win/draw/loss accumulation for group matches



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



    feature_cache = build_feature_cache(team_hist, elo_df)

    lambda_cache = build_lambda_cache(feature_cache, models)

    fixtures = get_group_fixtures()

    group_preds = [lambda_cache[(f["home_team"], f["away_team"])] for f in fixtures]



    acc = MonteCarloAccumulator()

    _run_monte_carlo_batch(

        acc,

        batch_start=0,

        batch_size=n_simulations,

        team_hist=team_hist,

        elo_df=elo_df,

        models=models,

        feature_cache=feature_cache,

        lambda_cache=lambda_cache,

        fixtures=fixtures,

        group_preds=group_preds,

        log_progress=True,

        progress_total=n_simulations,

    )



    return _finalize_monte_carlo_from_accumulator(acc, n_simulations)





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

            continue

        _extend_goal_store(home_goals, mid, np.array([res["home_goals"]], dtype=np.int32))

        _extend_goal_store(away_goals, mid, np.array([res["away_goals"]], dtype=np.int32))

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

