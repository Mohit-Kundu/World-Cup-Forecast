"""Tests for vectorized feature engineering and simulation helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.helpers import MatchRecord
from src.feature_engineering import (
    build_team_history_dfs,
    _get_rolling_rates,
    get_team_form,
    get_h2h_features,
    compute_dynamic_discipline,
)
from src.simulations import (
    build_lambda_cache,
    _draw_group_stage_batch,
    _accumulate_group_stage_batch,
    _group_standings_from_batch,
)
from src.models import PredictionBundle


def _make_record(
    date: str,
    home: str,
    away: str,
    home_score: int,
    away_score: int,
) -> MatchRecord:
    return MatchRecord(
        date=pd.Timestamp(date),
        home_team=home,
        away_team=away,
        home_score=home_score,
        away_score=away_score,
        tournament="Friendly",
        neutral=True,
    )


@pytest.fixture
def sample_team_hist():
    """Small synthetic history for Brazil and Argentina."""
    brazil_matches = [
        _make_record("2024-01-01", "Brazil", "Chile", 2, 0),
        _make_record("2024-02-01", "Uruguay", "Brazil", 1, 2),
        _make_record("2024-03-01", "Brazil", "Peru", 3, 1),
        _make_record("2024-04-01", "Colombia", "Brazil", 0, 0),
        _make_record("2024-05-01", "Brazil", "Argentina", 1, 2),
        _make_record("2024-06-01", "Brazil", "Paraguay", 2, 1),
    ]
    argentina_matches = [
        _make_record("2024-01-15", "Argentina", "Chile", 1, 0),
        _make_record("2024-02-15", "Uruguay", "Argentina", 2, 2),
        _make_record("2024-03-15", "Argentina", "Peru", 0, 1),
        _make_record("2024-04-15", "Argentina", "Colombia", 3, 0),
        _make_record("2024-05-01", "Brazil", "Argentina", 1, 2),
        _make_record("2024-06-15", "Argentina", "Paraguay", 2, 0),
    ]
    return {
        "Brazil": brazil_matches,
        "Argentina": argentina_matches,
    }


def test_build_team_history_dfs_shape(sample_team_hist):
    dfs = build_team_history_dfs(sample_team_hist)
    assert "Brazil" in dfs
    assert len(dfs["Brazil"]) == 6
    assert set(dfs["Brazil"].columns) >= {
        "date", "goals_scored", "goals_conceded", "points", "opponent", "opponent_elo"
    }


def test_rolling_rates_list_vs_df_equivalence(sample_team_hist):
    team_hist = sample_team_hist
    team_dfs = build_team_history_dfs(team_hist)
    current_date = pd.Timestamp("2025-01-01")

    for team in ("Brazil", "Argentina"):
        list_result = _get_rolling_rates(
            team_hist[team], team, current_date
        )
        df_result = _get_rolling_rates(
            team_hist[team], team, current_date,
            team_df=team_dfs[team],
        )
        assert list_result == pytest.approx(df_result)


def test_form_list_vs_df_equivalence(sample_team_hist):
    team_hist = sample_team_hist
    team_dfs = build_team_history_dfs(team_hist)
    current_date = pd.Timestamp("2025-01-01")

    for team in ("Brazil", "Argentina"):
        list_form = get_team_form(team_hist, team, current_date)
        df_form = get_team_form(team_hist, team, current_date, team_dfs=team_dfs)
        assert list_form == pytest.approx(df_form)


def test_h2h_list_vs_df_equivalence(sample_team_hist):
    team_hist = sample_team_hist
    team_dfs = build_team_history_dfs(team_hist)
    current_date = pd.Timestamp("2025-01-01")

    list_h2h = get_h2h_features(team_hist, "Brazil", "Argentina", current_date)
    df_h2h = get_h2h_features(
        team_hist, "Brazil", "Argentina", current_date, team_dfs=team_dfs
    )
    assert list_h2h == pytest.approx(df_h2h)


def test_discipline_list_vs_df_equivalence(sample_team_hist):
    team_hist = sample_team_hist
    team_dfs = build_team_history_dfs(team_hist)
    current_date = pd.Timestamp("2025-01-01")

    for team in ("Brazil", "Argentina"):
        list_disc = compute_dynamic_discipline(team_hist, team, current_date)
        df_disc = compute_dynamic_discipline(
            team_hist, team, current_date, team_dfs=team_dfs
        )
        assert list_disc == pytest.approx(df_disc)


def test_draw_group_stage_batch_shapes():
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
        for _ in range(3)
    ]
    draws = _draw_group_stage_batch(preds, n_simulations=100, seed=42)

    assert draws["home_goals"].shape == (100, 3)
    assert draws["away_goals"].shape == (100, 3)
    assert draws["home_red"].dtype == bool


def test_accumulate_group_stage_batch_counts():
    draws = {
        "home_goals": np.array([[2, 0], [1, 1], [0, 3]]),
        "away_goals": np.array([[1, 0], [1, 2], [1, 0]]),
    }
    fixtures = [
        {"match_id": 1, "home_team": "A", "away_team": "B", "group": "A"},
        {"match_id": 2, "home_team": "C", "away_team": "D", "group": "B"},
    ]
    home_goals: dict = {}
    away_goals: dict = {}
    home_wins: dict = {}
    draws_count: dict = {}
    away_wins: dict = {}
    metadata: dict = {}

    _accumulate_group_stage_batch(
        draws, fixtures, home_goals, away_goals,
        home_wins, draws_count, away_wins, metadata,
    )

    assert home_goals[1].tolist() == [2, 1, 0]
    assert home_wins[1] == 1
    assert draws_count[1] == 1
    assert away_wins[1] == 1
    assert home_wins[2] == 1
    assert draws_count[2] == 1
    assert away_wins[2] == 1
