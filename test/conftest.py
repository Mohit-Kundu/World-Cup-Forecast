"""Shared fixtures for FIFA WC prediction unit tests."""

from __future__ import annotations

import pandas as pd
import pytest

from src.helpers import MatchRecord


def make_record(
    date: str,
    home: str,
    away: str,
    home_score: int,
    away_score: int,
    tournament: str = "Friendly",
    neutral: bool = True,
) -> MatchRecord:
    return MatchRecord(
        date=pd.Timestamp(date),
        home_team=home,
        away_team=away,
        home_score=home_score,
        away_score=away_score,
        tournament=tournament,
        neutral=neutral,
    )


@pytest.fixture
def brazil_argentina_hist():
    """
    Controlled histories for hand-verified feature calculations.

    Brazil scored/conceded (chronological, team perspective):
      [2,0], [2,1], [3,1], [0,0], [1,2], [2,1]
    """
    brazil_matches = [
        make_record("2024-01-01", "Brazil", "Chile", 2, 0),
        make_record("2024-02-01", "Uruguay", "Brazil", 1, 2),
        make_record("2024-03-01", "Brazil", "Peru", 3, 1),
        make_record("2024-04-01", "Colombia", "Brazil", 0, 0),
        make_record("2024-05-01", "Brazil", "Argentina", 1, 2),
        make_record("2024-06-01", "Brazil", "Paraguay", 2, 1),
    ]
    argentina_matches = [
        make_record("2024-01-15", "Argentina", "Chile", 1, 0),
        make_record("2024-02-15", "Uruguay", "Argentina", 2, 2),
        make_record("2024-03-15", "Argentina", "Peru", 0, 1),
        make_record("2024-04-15", "Argentina", "Colombia", 3, 0),
        make_record("2024-05-01", "Brazil", "Argentina", 1, 2),
        make_record("2024-06-15", "Argentina", "Paraguay", 2, 0),
    ]
    return {
        "Brazil": brazil_matches,
        "Argentina": argentina_matches,
    }


@pytest.fixture
def eval_date():
    return pd.Timestamp("2025-01-01")


@pytest.fixture
def sample_pred():
    from src.models import PredictionBundle

    return PredictionBundle(
        home_goals_lambda=1.2,
        away_goals_lambda=0.8,
        home_yellow_lambda=2.0,
        away_yellow_lambda=1.5,
        home_red_prob=0.08,
        away_red_prob=0.06,
        home_corners_lambda=5.0,
        away_corners_lambda=4.0,
        home_elo=1650.0,
        away_elo=1550.0,
    )
