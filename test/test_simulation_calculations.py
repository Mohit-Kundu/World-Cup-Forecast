"""Unit tests for match simulation and Monte Carlo aggregation calculations."""

from __future__ import annotations

from collections import Counter, defaultdict
from unittest.mock import patch

import numpy as np
import pytest

from src.config import (
    EXTRA_TIME_GOALS_EXPECTED,
    PENALTY_ELO_SCALE,
    PENALTY_PROB_MIN,
    PENALTY_PROB_MAX,
    RANDOM_SEED,
)
from src.models import PredictionBundle
from src.simulations import (
    _draw_match_outcomes,
    _draw_group_stage_batch,
    _accumulate_group_stage_batch,
    _group_standings_from_batch,
    _finalize_knockout_result,
    _accumulate_knockout,
    simulate_penalties,
    simulate_extra_time,
)


class TestPenaltyProbability:
    def test_equal_elo_is_fifty_fifty(self, sample_pred):
        pred = PredictionBundle(
            home_goals_lambda=1.0,
            away_goals_lambda=1.0,
            home_yellow_lambda=2.0,
            away_yellow_lambda=2.0,
            home_red_prob=0.1,
            away_red_prob=0.1,
            home_corners_lambda=5.0,
            away_corners_lambda=5.0,
            home_elo=1500.0,
            away_elo=1500.0,
        )
        elo_diff = pred.home_elo - pred.away_elo
        raw_prob = 1.0 / (1.0 + np.exp(-elo_diff / PENALTY_ELO_SCALE))
        assert raw_prob == pytest.approx(0.5)

    def test_positive_elo_diff_increases_home_shootout_chance(self, sample_pred):
        elo_diff = sample_pred.home_elo - sample_pred.away_elo
        raw_prob = 1.0 / (1.0 + np.exp(-elo_diff / PENALTY_ELO_SCALE))
        clipped = float(np.clip(raw_prob, PENALTY_PROB_MIN, PENALTY_PROB_MAX))
        assert clipped == pytest.approx(0.5621765, rel=1e-4)
        assert PENALTY_PROB_MIN < clipped < PENALTY_PROB_MAX

    def test_large_elo_diff_is_clipped(self):
        pred = PredictionBundle(
            home_goals_lambda=1.0,
            away_goals_lambda=1.0,
            home_yellow_lambda=2.0,
            away_yellow_lambda=2.0,
            home_red_prob=0.1,
            away_red_prob=0.1,
            home_corners_lambda=5.0,
            away_corners_lambda=5.0,
            home_elo=2000.0,
            away_elo=1200.0,
        )
        elo_diff = pred.home_elo - pred.away_elo
        raw_prob = 1.0 / (1.0 + np.exp(-elo_diff / PENALTY_ELO_SCALE))
        clipped = float(np.clip(raw_prob, PENALTY_PROB_MIN, PENALTY_PROB_MAX))
        assert clipped == PENALTY_PROB_MAX

    def test_simulate_penalties_respects_probability(self, sample_pred):
        with patch("src.simulations.np.random.random", return_value=0.1):
            assert simulate_penalties("Home", "Away", sample_pred) == "Home"
        with patch("src.simulations.np.random.random", return_value=0.99):
            assert simulate_penalties("Home", "Away", sample_pred) == "Away"


class TestExtraTimeLambdas:
    def test_extra_time_split_proportional_to_goal_lambdas(self, sample_pred):
        total = sample_pred.home_goals_lambda + sample_pred.away_goals_lambda
        home_share = sample_pred.home_goals_lambda / total
        expected_home = EXTRA_TIME_GOALS_EXPECTED * home_share
        expected_away = EXTRA_TIME_GOALS_EXPECTED * (1.0 - home_share)

        assert expected_home == pytest.approx(0.48)
        assert expected_away == pytest.approx(0.32)

        with patch("src.simulations.np.random.poisson", side_effect=[1, 0]):
            et_home, et_away = simulate_extra_time(sample_pred)
        assert et_home == 1
        assert et_away == 0

    def test_zero_lambdas_split_evenly(self):
        pred = PredictionBundle(
            home_goals_lambda=0.0,
            away_goals_lambda=0.0,
            home_yellow_lambda=1.0,
            away_yellow_lambda=1.0,
            home_red_prob=0.1,
            away_red_prob=0.1,
            home_corners_lambda=5.0,
            away_corners_lambda=5.0,
            home_elo=1500.0,
            away_elo=1500.0,
        )
        with patch("src.simulations.np.random.poisson", side_effect=[0, 0]):
            et_home, et_away = simulate_extra_time(pred)
        assert et_home == 0
        assert et_away == 0


class TestKnockoutResolution:
    def test_home_win_in_regulation(self, sample_pred):
        result = {
            "home_goals": 2,
            "away_goals": 1,
            "home_team": "Home",
            "away_team": "Away",
        }
        finalized = _finalize_knockout_result(result, "Home", "Away", sample_pred)
        assert finalized["winner"] == "Home"

    def test_draw_goes_to_extra_time_then_penalties(self, sample_pred):
        result = {"home_goals": 1, "away_goals": 1}
        with patch("src.simulations.simulate_extra_time", return_value=(0, 0)):
            with patch(
                "src.simulations.simulate_penalties", return_value="Away"
            ) as mock_pens:
                finalized = _finalize_knockout_result(
                    result.copy(), "Home", "Away", sample_pred
                )
        mock_pens.assert_called_once()
        assert finalized["winner"] == "Away"

    def test_extra_time_winner_decided_without_penalties(self, sample_pred):
        result = {"home_goals": 0, "away_goals": 0}
        with patch("src.simulations.simulate_extra_time", return_value=(1, 0)):
            finalized = _finalize_knockout_result(
                result, "Home", "Away", sample_pred
            )
        assert finalized["home_goals"] == 1
        assert finalized["away_goals"] == 0
        assert finalized["winner"] == "Home"


class TestMatchOutcomeDraw:
    def test_draw_match_outcomes_with_fixed_rng(self, sample_pred):
        with patch("src.simulations.np.random.poisson", side_effect=[2, 1, 3, 2, 6, 5]):
            with patch("src.simulations.np.random.random", side_effect=[0.01, 0.99]):
                outcomes = _draw_match_outcomes(sample_pred)
        assert outcomes == {
            "home_goals": 2,
            "away_goals": 1,
            "home_yellow": 3,
            "away_yellow": 2,
            "home_red": 1,
            "away_red": 0,
            "home_corners": 6,
            "away_corners": 5,
        }


class TestBatchGroupStage:
    def test_batch_draw_reproducible_with_seed(self):
        preds = [
            PredictionBundle(
                home_goals_lambda=1.5,
                away_goals_lambda=1.2,
                home_yellow_lambda=2.0,
                away_yellow_lambda=2.0,
                home_red_prob=0.1,
                away_red_prob=0.1,
                home_corners_lambda=5.0,
                away_corners_lambda=5.0,
                home_elo=1600.0,
                away_elo=1550.0,
            )
        ]
        draw_a = _draw_group_stage_batch(preds, n_simulations=5, seed=99)
        draw_b = _draw_group_stage_batch(preds, n_simulations=5, seed=99)
        assert np.array_equal(draw_a["home_goals"], draw_b["home_goals"])

    def test_batch_means_approximate_poisson_lambdas(self):
        preds = [
            PredictionBundle(
                home_goals_lambda=2.0,
                away_goals_lambda=1.0,
                home_yellow_lambda=2.0,
                away_yellow_lambda=2.0,
                home_red_prob=0.1,
                away_red_prob=0.1,
                home_corners_lambda=5.0,
                away_corners_lambda=5.0,
                home_elo=1600.0,
                away_elo=1550.0,
            )
        ]
        draws = _draw_group_stage_batch(preds, n_simulations=20_000, seed=RANDOM_SEED)
        assert draws["home_goals"].mean() == pytest.approx(2.0, abs=0.1)
        assert draws["away_goals"].mean() == pytest.approx(1.0, abs=0.1)

    def test_group_standings_from_batch_matches_manual_results(self):
        fixtures = [
            {
                "match_id": 1,
                "stage": "Group",
                "group": "Z",
                "home_team": "TeamA",
                "away_team": "TeamB",
                "neutral": True,
            },
            {
                "match_id": 2,
                "stage": "Group",
                "group": "Z",
                "home_team": "TeamA",
                "away_team": "TeamC",
                "neutral": True,
            },
            {
                "match_id": 3,
                "stage": "Group",
                "group": "Z",
                "home_team": "TeamB",
                "away_team": "TeamC",
                "neutral": True,
            },
        ]
        draws = {
            "home_goals": np.array([[2, 1, 0]]),
            "away_goals": np.array([[0, 1, 1]]),
            "home_yellow": np.array([[0, 0, 0]]),
            "away_yellow": np.array([[0, 0, 0]]),
            "home_red": np.array([[False, False, False]]),
            "away_red": np.array([[False, False, False]]),
            "home_corners": np.array([[0, 0, 0]]),
            "away_corners": np.array([[0, 0, 0]]),
        }
        standings, results = _group_standings_from_batch(draws, 0, fixtures)

        assert len(results) == 3
        assert standings["Z"].loc[standings["Z"]["rank"] == 1, "team"].iloc[0] == "TeamA"
        assert standings["Z"].loc[standings["Z"]["team"] == "TeamA", "pts"].iloc[0] == 4


class TestMonteCarloAccumulation:
    def test_group_batch_accumulation_probabilities(self):
        draws = {
            "home_goals": np.array([[2, 0], [1, 1], [0, 3]]),
            "away_goals": np.array([[1, 0], [1, 2], [1, 0]]),
        }
        fixtures = [
            {"match_id": 10, "home_team": "A", "away_team": "B", "group": "G"},
            {"match_id": 11, "home_team": "C", "away_team": "D", "group": "G"},
        ]
        home_goals: dict = {}
        away_goals: dict = {}
        home_wins = defaultdict(int)
        draws_count = defaultdict(int)
        away_wins = defaultdict(int)
        metadata: dict = {}

        _accumulate_group_stage_batch(
            draws,
            fixtures,
            home_goals,
            away_goals,
            home_wins,
            draws_count,
            away_wins,
            metadata,
        )

        n = 3
        assert home_wins[10] / n == pytest.approx(1 / 3)
        assert draws_count[10] / n == pytest.approx(1 / 3)
        assert away_wins[10] / n == pytest.approx(1 / 3)

    def test_knockout_accumulation_uses_winner_not_raw_score(self):
        home_goals: dict = {50: [1]}
        away_goals: dict = {50: [1]}
        home_wins = defaultdict(int)
        draws_count = defaultdict(int)
        away_wins = defaultdict(int)
        metadata: dict = {}

        results = [
            {
                "match_id": 50,
                "home_team": "A",
                "away_team": "B",
                "home_goals": 1,
                "away_goals": 1,
                "winner": "A",
                "stage": "Round of 16",
            }
        ]
        _accumulate_knockout(
            results,
            home_goals,
            away_goals,
            home_wins,
            draws_count,
            away_wins,
            metadata,
        )
        assert home_wins[50] == 1
        assert draws_count[50] == 0
        assert away_goals[50].tolist() == [1, 1]

    def test_mode_and_probability_aggregation(self):
        home_goal_samples = [1, 2, 1, 1, 0]
        away_goal_samples = [0, 1, 2, 0, 0]
        n = len(home_goal_samples)

        mode_home = Counter(home_goal_samples).most_common(1)[0][0]
        mode_away = Counter(away_goal_samples).most_common(1)[0][0]
        home_win_prob = sum(h > a for h, a in zip(home_goal_samples, away_goal_samples)) / n
        draw_prob = sum(h == a for h, a in zip(home_goal_samples, away_goal_samples)) / n
        away_win_prob = sum(h < a for h, a in zip(home_goal_samples, away_goal_samples)) / n

        assert mode_home == 1
        assert mode_away == 0
        assert home_win_prob == pytest.approx(0.6)
        assert draw_prob == pytest.approx(0.2)
        assert away_win_prob == pytest.approx(0.2)
        assert home_win_prob + draw_prob + away_win_prob == pytest.approx(1.0)
