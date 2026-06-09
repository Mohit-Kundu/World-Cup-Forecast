"""Integration smoke test for parallel knockout engine."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.knockout_engine import merge_knockout_results, run_knockout_loop_parallel
from src.simulations import MonteCarloAccumulator, _draw_group_stage_batch
from src.helpers import get_group_fixtures
from src.models import PredictionBundle


def _dummy_pred() -> PredictionBundle:
    return PredictionBundle(
        home_goals_lambda=1.3,
        away_goals_lambda=1.1,
        home_yellow_lambda=2.0,
        away_yellow_lambda=2.0,
        home_red_prob=0.05,
        away_red_prob=0.05,
        home_corners_lambda=5.0,
        away_corners_lambda=5.0,
        home_elo=1600.0,
        away_elo=1550.0,
    )


@pytest.mark.parametrize("batch_size", [4, 8])
def test_parallel_knockout_loop_runs(batch_size: int):
    fixtures = get_group_fixtures()
    preds = [_dummy_pred() for _ in fixtures]
    group_draws = _draw_group_stage_batch(preds, n_simulations=batch_size, seed=42)

    acc = MonteCarloAccumulator()
    dummy_models = MagicMock()
    dummy_hist: dict = {}
    dummy_elo: dict = {}

    with patch("src.knockout_engine.MC_N_JOBS", 1), patch(
        "src.knockout_engine._simulate_knockout_path"
    ) as mock_path:
        from src.knockout_engine import SingleKnockoutSimResult

        mock_path.return_value = SingleKnockoutSimResult(
            qualify_teams=["Brazil", "France"],
            r32_winners=["Brazil"],
            r16_winners=["Brazil"],
            qf_winners=["Brazil"],
            sf_winners=["Brazil", "France"],
            final_winner="Brazil",
            final_pairing=("Brazil", "France"),
            knockout_results=[],
        )

        run_knockout_loop_parallel(
            acc,
            group_draws,
            fixtures,
            batch_start=0,
            batch_size=batch_size,
            team_hist=dummy_hist,
            elo_df=dummy_elo,
            models=dummy_models,
            feature_cache={},
            lambda_cache={},
            log_progress=False,
        )

    assert mock_path.call_count == batch_size
    assert acc.champion_counter["Brazil"] == batch_size
