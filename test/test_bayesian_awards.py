"""Tests for ELO-adjusted Bayesian attack/defense award metrics."""

from __future__ import annotations

import pytest

from src.feature_engineering import (
    bayesian_smoothed_raw_rate,
    bayesian_smoothed_rate,
    elo_adjusted_attack_score,
    elo_adjusted_fortress_score,
)
from src.wrapped_awards import _build_fortress, _build_lethal_attack


def test_bayesian_smoothed_rate_pulls_small_samples_toward_prior():
    rate = bayesian_smoothed_rate(total=0, games=2, global_avg=1.10, weight=5)
    assert rate == pytest.approx(0.786, abs=0.001)

    proven = bayesian_smoothed_rate(total=3, games=10, global_avg=1.10, weight=5)
    assert proven == pytest.approx(0.567, abs=0.001)
    assert proven < rate


def test_elo_adjusted_scores_favor_stronger_teams():
    mean_elo = 1800.0
    smoothed_attack = 2.0
    high_elo_attack = elo_adjusted_attack_score(smoothed_attack, 2100.0, mean_elo)
    low_elo_attack = elo_adjusted_attack_score(smoothed_attack, 1500.0, mean_elo)
    assert high_elo_attack > low_elo_attack

    smoothed_conceded = 0.5
    high_elo_fortress = elo_adjusted_fortress_score(smoothed_conceded, 2100.0, mean_elo)
    low_elo_fortress = elo_adjusted_fortress_score(smoothed_conceded, 1500.0, mean_elo)
    assert high_elo_fortress < low_elo_fortress


def test_lethal_attack_uses_elo_adjusted_score_and_raw_display():
    team_stats = {
        "Spain": {
            "FIFA ELO Rating": "2165",
            "Rolling Attack Rate": "3.10",
            "ELO-Adjusted Attack Score": "3.254",
            "Rolling Match Count": "10",
            "Last 5 Goals Scored": "14",
        },
        "Belgium": {
            "FIFA ELO Rating": "1867",
            "Rolling Attack Rate": "3.50",
            "ELO-Adjusted Attack Score": "3.085",
            "Rolling Match Count": "10",
            "Last 5 Goals Scored": "15",
        },
    }

    card = _build_lethal_attack(team_stats)

    assert card["teams"] == ["Spain"]
    assert card["bigNumber"] == "3.10"
    assert "14 goals" in card["insight"]


def test_fortress_uses_elo_adjusted_score_and_raw_display():
    team_stats = {
        "Argentina": {
            "FIFA ELO Rating": "2113",
            "Rolling Conceded Rate": "0.40",
            "ELO-Adjusted Fortress Score": "0.489",
            "Rolling Match Count": "10",
            "Avg Opponent ELO (Rolling)": "1820",
        },
        "DR Congo": {
            "FIFA ELO Rating": "1655",
            "Rolling Conceded Rate": "0.30",
            "ELO-Adjusted Fortress Score": "0.553",
            "Rolling Match Count": "2",
            "Avg Opponent ELO (Rolling)": "1500",
        },
    }

    card = _build_fortress(team_stats)

    assert card["teams"] == ["Argentina"]
    assert card["bigNumber"] == "0.40"
    assert "team ELO 2113" in card["insight"]


def test_bayesian_smoothed_raw_rate_matches_total_form():
    raw = bayesian_smoothed_raw_rate(2.0, 10, 1.25, 5)
    total = bayesian_smoothed_rate(20.0, 10, 1.25, 5)
    assert raw == pytest.approx(total)
