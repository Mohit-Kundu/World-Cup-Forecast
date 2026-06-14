"""
src/knockout_engine.py
======================
Parallel knockout simulation with explicit RNG streams.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from joblib import Parallel, delayed

from src.config import MC_N_JOBS, RANDOM_SEED
from src.helpers import build_knockout_bracket
from src.models import ModelBundle, PredictionBundle

FeatureCache = Dict[Tuple[str, str], Any]
LambdaCache = Dict[Tuple[str, str], PredictionBundle]

KNOCKOUT_STAGES = {
    "Round of 32",
    "Round of 16",
    "Quarter-Final",
    "Semi-Final",
    "Final",
}


def _is_knockout_upset(
    winner: str,
    home_team: str,
    away_team: str,
    elo_dict: Dict[str, float],
) -> bool:
    winner_elo = elo_dict.get(winner, 1500.0)
    opponent = away_team if winner == home_team else home_team
    opponent_elo = elo_dict.get(opponent, 1500.0)
    return winner_elo < opponent_elo


def _count_knockout_upsets(
    knockout_results: List[Dict[str, Any]],
    elo_dict: Dict[str, float],
) -> Counter:
    upsets: Counter = Counter()
    for result in knockout_results:
        stage = result.get("stage")
        if stage not in KNOCKOUT_STAGES:
            continue
        winner = result.get("winner")
        home_team = result.get("home_team")
        away_team = result.get("away_team")
        if not winner or not home_team or not away_team:
            continue
        if _is_knockout_upset(winner, home_team, away_team, elo_dict):
            upsets[winner] += 1
    return upsets


@dataclass
class SingleKnockoutSimResult:
    """Counters and knockout match rows from one MC iteration."""

    qualify_teams: List[str] = field(default_factory=list)
    r32_winners: List[str] = field(default_factory=list)
    r16_winners: List[str] = field(default_factory=list)
    qf_winners: List[str] = field(default_factory=list)
    sf_winners: List[str] = field(default_factory=list)
    final_winner: Optional[str] = None
    final_pairing: Optional[Tuple[str, str]] = None
    knockout_results: List[Dict[str, Any]] = field(default_factory=list)
    upset_wins: Counter = field(default_factory=Counter)


def _draw_match_outcomes(
    pred: PredictionBundle,
    rng: np.random.Generator,
) -> Dict[str, int]:
    return {
        "home_goals": int(rng.poisson(pred.home_goals_lambda)),
        "away_goals": int(rng.poisson(pred.away_goals_lambda)),
        "home_yellow": int(rng.poisson(max(pred.home_yellow_lambda, 0.01))),
        "away_yellow": int(rng.poisson(max(pred.away_yellow_lambda, 0.01))),
        "home_red": int(rng.random() < pred.home_red_prob),
        "away_red": int(rng.random() < pred.away_red_prob),
        "home_corners": int(rng.poisson(max(pred.home_corners_lambda, 1.0))),
        "away_corners": int(rng.poisson(max(pred.away_corners_lambda, 1.0))),
    }


def _simulate_extra_time(
    pred: PredictionBundle,
    rng: np.random.Generator,
) -> Tuple[int, int]:
    from src.config import EXTRA_TIME_GOALS_EXPECTED

    total_lambda = pred.home_goals_lambda + pred.away_goals_lambda
    home_share = 0.5 if total_lambda < 1e-6 else pred.home_goals_lambda / total_lambda
    home_et_lambda = EXTRA_TIME_GOALS_EXPECTED * home_share
    away_et_lambda = EXTRA_TIME_GOALS_EXPECTED * (1.0 - home_share)
    return (
        int(rng.poisson(home_et_lambda)),
        int(rng.poisson(away_et_lambda)),
    )


def _simulate_penalties(
    home_team: str,
    away_team: str,
    pred: PredictionBundle,
    rng: np.random.Generator,
) -> str:
    from src.config import PENALTY_ELO_SCALE, PENALTY_PROB_MIN, PENALTY_PROB_MAX

    elo_diff = pred.home_elo - pred.away_elo
    shootout_prob = 1.0 / (1.0 + np.exp(-elo_diff / PENALTY_ELO_SCALE))
    shootout_prob = float(np.clip(shootout_prob, PENALTY_PROB_MIN, PENALTY_PROB_MAX))
    return home_team if rng.random() < shootout_prob else away_team


def _finalize_knockout_result(
    result: Dict[str, Any],
    home_team: str,
    away_team: str,
    pred: PredictionBundle,
    rng: np.random.Generator,
) -> Dict[str, Any]:
    hg, ag = result["home_goals"], result["away_goals"]

    if hg == ag:
        et_home, et_away = _simulate_extra_time(pred, rng)
        hg += et_home
        ag += et_away
        result["home_goals"] = hg
        result["away_goals"] = ag

    if hg == ag:
        result["winner"] = _simulate_penalties(home_team, away_team, pred, rng)
    elif hg > ag:
        result["winner"] = home_team
    else:
        result["winner"] = away_team

    return result


def _simulate_match(
    home_team: str,
    away_team: str,
    team_hist: Dict,
    elo_dict: Dict[str, float],
    models: ModelBundle,
    knockout: bool,
    rng: np.random.Generator,
    feature_cache: Optional[FeatureCache] = None,
    lambda_cache: Optional[LambdaCache] = None,
) -> Dict[str, Any]:
    from src.simulations import _lookup_pred

    pred = _lookup_pred(
        home_team,
        away_team,
        team_hist,
        elo_dict,
        models,
        feature_cache=feature_cache,
        lambda_cache=lambda_cache,
    )
    result = _draw_match_outcomes(pred, rng)
    result["home_team"] = home_team
    result["away_team"] = away_team

    if knockout:
        result = _finalize_knockout_result(result, home_team, away_team, pred, rng)

    return result


def _simulate_knockout_round(
    matchups: List[Dict],
    team_hist: Dict,
    elo_dict: Dict[str, float],
    models: ModelBundle,
    stage_name: str,
    rng: np.random.Generator,
    feature_cache: Optional[FeatureCache] = None,
    lambda_cache: Optional[LambdaCache] = None,
) -> Tuple[List[str], List[Dict]]:
    winners: List[str] = []
    round_results: List[Dict] = []

    for match in matchups:
        result = _simulate_match(
            home_team=match["home_team"],
            away_team=match["away_team"],
            team_hist=team_hist,
            elo_dict=elo_dict,
            models=models,
            knockout=True,
            rng=rng,
            feature_cache=feature_cache,
            lambda_cache=lambda_cache,
        )
        result["stage"] = stage_name
        result["match_id"] = match.get("match_id", -1)
        winners.append(result["winner"])
        round_results.append(result)

    return winners, round_results


def _simulate_knockout_path(
    local_i: int,
    batch_start: int,
    group_draws: Dict[str, np.ndarray],
    fixtures: List[Dict],
    team_hist: Dict,
    elo_df: Dict[str, float],
    models: ModelBundle,
    feature_cache: FeatureCache,
    lambda_cache: LambdaCache,
) -> SingleKnockoutSimResult:
    from src.simulations import _group_standings_from_batch, _pair_winners

    rng = np.random.default_rng(RANDOM_SEED + batch_start + local_i)
    out = SingleKnockoutSimResult()

    group_standings, _ = _group_standings_from_batch(
        group_draws, local_i, fixtures, rng=rng
    )

    for standings_df in group_standings.values():
        top_two = standings_df.loc[standings_df["rank"] <= 2, "team"].tolist()
        out.qualify_teams.extend(top_two)

    r32_matchups = build_knockout_bracket(group_standings)
    r32_winners, r32_results = _simulate_knockout_round(
        r32_matchups, team_hist, elo_df, models, "Round of 32", rng,
        feature_cache=feature_cache, lambda_cache=lambda_cache,
    )
    out.r32_winners = r32_winners
    out.knockout_results.extend(r32_results)

    r16_matchups = _pair_winners(r32_winners, start_match_id=65, stage="Round of 16")
    r16_winners, r16_results = _simulate_knockout_round(
        r16_matchups, team_hist, elo_df, models, "Round of 16", rng,
        feature_cache=feature_cache, lambda_cache=lambda_cache,
    )
    out.r16_winners = r16_winners
    out.knockout_results.extend(r16_results)

    qf_matchups = _pair_winners(r16_winners, start_match_id=73, stage="Quarter-Final")
    qf_winners, qf_results = _simulate_knockout_round(
        qf_matchups, team_hist, elo_df, models, "Quarter-Final", rng,
        feature_cache=feature_cache, lambda_cache=lambda_cache,
    )
    out.qf_winners = qf_winners
    out.knockout_results.extend(qf_results)

    sf_matchups = _pair_winners(qf_winners, start_match_id=77, stage="Semi-Final")
    sf_winners, sf_results = _simulate_knockout_round(
        sf_matchups, team_hist, elo_df, models, "Semi-Final", rng,
        feature_cache=feature_cache, lambda_cache=lambda_cache,
    )
    out.sf_winners = sf_winners
    out.knockout_results.extend(sf_results)

    if len(sf_winners) >= 2:
        home_final, away_final = sf_winners[0], sf_winners[1]
        out.final_pairing = (home_final, away_final)
        final_matchup = [{
            "match_id": 79,
            "stage": "Final",
            "home_team": home_final,
            "away_team": away_final,
            "neutral": True,
        }]
        final_winners, final_results = _simulate_knockout_round(
            final_matchup, team_hist, elo_df, models, "Final", rng,
            feature_cache=feature_cache, lambda_cache=lambda_cache,
        )
        out.knockout_results.extend(final_results)
        if final_winners:
            out.final_winner = final_winners[0]

    out.upset_wins = _count_knockout_upsets(out.knockout_results, elo_df)
    return out


def _chunk_indices(batch_size: int, n_chunks: int) -> List[List[int]]:
    n_chunks = max(1, min(n_chunks, batch_size))
    chunk_size = max(1, (batch_size + n_chunks - 1) // n_chunks)
    return [
        list(range(start, min(start + chunk_size, batch_size)))
        for start in range(0, batch_size, chunk_size)
    ]


def _run_knockout_chunk(
    indices: List[int],
    batch_start: int,
    group_draws: Dict[str, np.ndarray],
    fixtures: List[Dict],
    team_hist: Dict,
    elo_df: Dict[str, float],
    models: ModelBundle,
    feature_cache: FeatureCache,
    lambda_cache: LambdaCache,
) -> List[SingleKnockoutSimResult]:
    return [
        _simulate_knockout_path(
            local_i, batch_start, group_draws, fixtures,
            team_hist, elo_df, models, feature_cache, lambda_cache,
        )
        for local_i in indices
    ]


def merge_knockout_results(
    acc: Any,
    sim_results: List[SingleKnockoutSimResult],
) -> None:
    """Merge per-simulation knockout outputs into MonteCarloAccumulator."""
    from src.simulations import _accumulate_knockout

    for sim in sim_results:
        for team in sim.qualify_teams:
            acc.qualify_counter[team] += 1
        for team in sim.r32_winners:
            acc.r32_counter[team] += 1
        for team in sim.r16_winners:
            acc.r16_counter[team] += 1
        for team in sim.qf_winners:
            acc.qf_counter[team] += 1
        for team in sim.sf_winners:
            acc.finalist_counter[team] += 1
            acc.sf_counter[team] += 1
        if sim.final_pairing is not None:
            acc.final_pairing_counter[sim.final_pairing] += 1
        if sim.final_winner is not None and sim.final_pairing is not None:
            acc.champion_counter[sim.final_winner] += 1
            acc.final_winner_by_pairing[sim.final_pairing][sim.final_winner] += 1
        _accumulate_knockout(
            sim.knockout_results,
            acc.match_home_goals,
            acc.match_away_goals,
            acc.match_home_wins,
            acc.match_draws,
            acc.match_away_wins,
            acc.match_metadata,
        )
        for team, count in sim.upset_wins.items():
            acc.team_upset_counter[team] += count


def run_knockout_loop_parallel(
    acc: Any,
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
    """Run knockout rounds for a batch using joblib parallelism."""
    import logging

    logger = logging.getLogger(__name__)

    n_workers = MC_N_JOBS if MC_N_JOBS > 0 else -1
    n_chunks = batch_size if n_workers == -1 else max(n_workers * 4, 1)
    chunks = _chunk_indices(batch_size, n_chunks)

    chunk_outputs = Parallel(n_jobs=n_workers, prefer="processes")(
        delayed(_run_knockout_chunk)(
            chunk,
            batch_start,
            group_draws,
            fixtures,
            team_hist,
            elo_df,
            models,
            feature_cache,
            lambda_cache,
        )
        for chunk in chunks
    )

    flat_results: List[SingleKnockoutSimResult] = [
        sim for chunk in chunk_outputs for sim in chunk
    ]
    merge_knockout_results(acc, flat_results)

    if log_progress:
        total = progress_total if progress_total is not None else batch_start + batch_size
        logger.info("  Knockout batch done: %s / %s", f"{batch_start + batch_size:,}", f"{total:,}")
