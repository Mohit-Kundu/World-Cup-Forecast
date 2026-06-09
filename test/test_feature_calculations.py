"""Unit tests for feature-engineering calculations with known expected values."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.helpers import MatchRecord
from src.feature_engineering import (
    _rolling_rates_from_scored_conceded,
    _get_rolling_rates,
    get_team_form,
    get_h2h_features,
    compute_dynamic_discipline,
    compute_recency_weights,
    _get_tournament_weight,
    _build_match_features,
    build_team_history_dfs,
    _quality_adjusted_form,
    ELO_BASELINE,
)


def make_record(date, home, away, home_score, away_score, home_elo=1500.0, away_elo=1500.0):
    return MatchRecord(
        date=pd.Timestamp(date),
        home_team=home,
        away_team=away,
        home_score=home_score,
        away_score=away_score,
        tournament="Friendly",
        neutral=True,
        home_elo=home_elo,
        away_elo=away_elo,
    )


class TestRollingRatesFromArrays:
    """Direct tests for the core rolling-rate formula."""

    def test_empty_history_returns_neutral(self):
        attack, defense = _rolling_rates_from_scored_conceded(
            np.array([]), np.array([])
        )
        assert attack == 1.0
        assert defense == 1.0

    def test_small_sample_blends_toward_neutral(self):
        scored = np.array([2.0, 0.0, 1.0])
        conceded = np.array([0.0, 2.0, 1.0])
        blend = 3 / 5.0
        expected_attack = blend * np.mean(scored) + (1 - blend) * 1.0
        expected_conceded = blend * np.mean(conceded) + (1 - blend) * 1.0
        expected_defense = 1.0 / max(expected_conceded, 0.1)

        attack, defense = _rolling_rates_from_scored_conceded(scored, conceded)
        assert attack == pytest.approx(expected_attack)
        assert defense == pytest.approx(expected_defense)

    def test_six_match_window_uses_70_30_split(self):
        scored = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 5.0])
        conceded = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 3.0])
        recent5 = scored[-5:]
        prior = scored[:-5]
        expected_attack = 0.70 * np.mean(recent5) + 0.30 * np.mean(prior)
        recent5c = conceded[-5:]
        priorc = conceded[:-5]
        expected_conceded = 0.70 * np.mean(recent5c) + 0.30 * np.mean(priorc)
        expected_defense = 1.0 / max(expected_conceded, 0.1)

        attack, defense = _rolling_rates_from_scored_conceded(scored, conceded)
        assert attack == pytest.approx(expected_attack)
        assert defense == pytest.approx(expected_defense)


class TestTeamFeatureCalculations:
    """Hand-verified calculations on the Brazil/Argentina fixture histories."""

    def test_brazil_rolling_rates(self, brazil_argentina_hist, eval_date):
        history = brazil_argentina_hist["Brazil"]
        scored = np.array([2, 2, 3, 0, 1, 2], dtype=float)
        conceded = np.array([0, 1, 1, 0, 2, 1], dtype=float)
        recent5 = scored[-5:]
        prior = scored[:-5]
        expected_attack = 0.70 * np.mean(recent5) + 0.30 * np.mean(prior)
        recent5c = conceded[-5:]
        priorc = conceded[:-5]
        expected_conceded = 0.70 * np.mean(recent5c) + 0.30 * np.mean(priorc)
        expected_defense = 1.0 / max(expected_conceded, 0.1)

        attack, defense = _get_rolling_rates(history, "Brazil", eval_date)
        assert attack == pytest.approx(expected_attack)
        assert defense == pytest.approx(expected_defense)

    def test_brazil_form_index(self, brazil_argentina_hist, eval_date):
        # Last 5 Brazil results: W, W, D, L, W -> points [3,3,1,0,3] -> mean 2.0 -> 2/3
        form = get_team_form(brazil_argentina_hist, "Brazil", eval_date)
        assert form == pytest.approx(2.0 / 3.0)

    def test_argentina_form_index(self, brazil_argentina_hist, eval_date):
        # Last 5 Argentina results: D, L, W, W, W -> points [1,0,3,3,3] -> mean 2.0 -> 2/3
        form = get_team_form(brazil_argentina_hist, "Argentina", eval_date)
        assert form == pytest.approx(2.0 / 3.0)

    def test_h2h_brazil_vs_argentina(self, brazil_argentina_hist, eval_date):
        win_rate, avg_gd = get_h2h_features(
            brazil_argentina_hist, "Brazil", "Argentina", eval_date
        )
        assert win_rate == pytest.approx(0.0)
        assert avg_gd == pytest.approx(-1.0)

    def test_h2h_no_history_returns_neutral(self, brazil_argentina_hist, eval_date):
        win_rate, avg_gd = get_h2h_features(
            brazil_argentina_hist, "Brazil", "Japan", eval_date
        )
        assert win_rate == pytest.approx(0.5)
        assert avg_gd == pytest.approx(0.0)

    def test_brazil_discipline_proxy(self, brazil_argentina_hist, eval_date):
        conceded = np.array([0, 1, 1, 0, 2, 1], dtype=float)
        avg_conceded = float(np.mean(conceded))
        expected = float(np.clip(1.0 + avg_conceded * 1.2, 0.5, 4.5))

        discipline = compute_dynamic_discipline(
            brazil_argentina_hist, "Brazil", eval_date
        )
        assert discipline == pytest.approx(expected)

    def test_no_history_returns_defaults(self, eval_date):
        attack, defense = _get_rolling_rates([], "Unknown", eval_date)
        assert attack == 1.0
        assert defense == 1.0
        assert get_team_form({}, "Unknown", eval_date) == 0.5
        assert compute_dynamic_discipline({}, "Unknown", eval_date) == 2.0

    def test_list_and_dataframe_backends_agree(self, brazil_argentina_hist, eval_date):
        team_dfs = build_team_history_dfs(brazil_argentina_hist)
        for team in ("Brazil", "Argentina"):
            list_rates = _get_rolling_rates(
                brazil_argentina_hist[team], team, eval_date
            )
            df_rates = _get_rolling_rates(
                brazil_argentina_hist[team],
                team,
                eval_date,
                team_df=team_dfs[team],
            )
            assert list_rates == pytest.approx(df_rates)

            assert get_team_form(
                brazil_argentina_hist, team, eval_date
            ) == pytest.approx(
                get_team_form(
                    brazil_argentina_hist, team, eval_date, team_dfs=team_dfs
                )
            )


class TestRecencyWeights:
    def test_current_year_weight_is_one(self):
        df = pd.DataFrame({"date": [pd.Timestamp("2026-06-01")]})
        weights = compute_recency_weights(df, current_year=2026)
        assert weights[0] == pytest.approx(1.0)

    def test_half_life_halves_weight(self):
        df = pd.DataFrame({"date": [pd.Timestamp("2011-06-01")]})
        weights = compute_recency_weights(df, current_year=2026, half_life_years=15.0)
        assert weights[0] == pytest.approx(0.5)

    def test_floor_at_minimum_weight(self):
        df = pd.DataFrame({"date": [pd.Timestamp("1900-01-01")]})
        weights = compute_recency_weights(df, current_year=2026)
        assert weights[0] == pytest.approx(0.05)


class TestMatchFeatureAssembly:
    def test_tournament_weight_lookup(self):
        assert _get_tournament_weight("FIFA World Cup Final") == 1.30
        assert _get_tournament_weight("International Friendly") == 1.00

    def test_host_nation_flag_only_when_not_neutral(self, brazil_argentina_hist):
        row = pd.Series(
            {
                "home_team": "Mexico",
                "away_team": "Brazil",
                "date": pd.Timestamp("2026-06-11"),
                "home_elo": 1600.0,
                "away_elo": 1700.0,
                "tournament": "FIFA World Cup",
                "neutral": False,
            }
        )
        feats = _build_match_features(row, brazil_argentina_hist)
        assert feats["is_host"] == 1
        assert feats["elo_diff"] == pytest.approx(-100.0)
        assert feats["tournament_weight"] == 1.30

    def test_neutral_host_match_not_flagged_as_host(self, brazil_argentina_hist):
        row = pd.Series(
            {
                "home_team": "Mexico",
                "away_team": "Brazil",
                "date": pd.Timestamp("2026-06-11"),
                "home_elo": 1600.0,
                "away_elo": 1700.0,
                "tournament": "FIFA World Cup",
                "neutral": True,
            }
        )
        feats = _build_match_features(row, brazil_argentina_hist)
        assert feats["is_host"] == 0

    def test_excludes_matches_on_or_after_eval_date(self, eval_date):
        hist = {
            "TeamX": [
                make_record("2024-01-01", "TeamX", "A", 3, 0),
                make_record("2025-06-01", "TeamX", "B", 0, 5),
            ]
        }
        attack, _ = _get_rolling_rates(hist["TeamX"], "TeamX", eval_date)
        # Only the 3-0 counts (blend=1/5): 0.2*3 + 0.8*1 = 1.4
        assert attack == pytest.approx(1.4)


class TestOpponentEloWeighting:
    """Verify quality-adjusted form and rolling rates respond to opponent Elo."""

    def test_form_beating_strong_teams_scores_higher(self, eval_date):
        # Same 1W + 4L record; win vs elite should beat win vs minnow
        win_vs_weak = {
            "TeamA": [
                make_record("2024-01-01", "TeamA", "Elite", 0, 2, away_elo=1800.0),
                make_record("2024-02-01", "TeamA", "Minnow", 2, 0, away_elo=1200.0),
                make_record("2024-03-01", "TeamA", "Minnow", 0, 1, away_elo=1200.0),
                make_record("2024-04-01", "TeamA", "Minnow", 0, 1, away_elo=1200.0),
                make_record("2024-05-01", "TeamA", "Minnow", 0, 1, away_elo=1200.0),
            ]
        }
        win_vs_elite = {
            "TeamA": [
                make_record("2024-01-01", "TeamA", "Elite", 2, 0, away_elo=1800.0),
                make_record("2024-02-01", "TeamA", "Minnow", 0, 1, away_elo=1200.0),
                make_record("2024-03-01", "TeamA", "Minnow", 0, 1, away_elo=1200.0),
                make_record("2024-04-01", "TeamA", "Minnow", 0, 1, away_elo=1200.0),
                make_record("2024-05-01", "TeamA", "Minnow", 0, 1, away_elo=1200.0),
            ]
        }
        weak_form = get_team_form(win_vs_weak, "TeamA", eval_date)
        strong_form = get_team_form(win_vs_elite, "TeamA", eval_date)
        assert strong_form > weak_form

    def test_form_all_neutral_elo_matches_unweighted(self):
        points = np.array([3.0, 3.0, 1.0, 0.0, 3.0])
        elos = np.full(5, ELO_BASELINE)
        assert _quality_adjusted_form(points, elos) == pytest.approx(2.0 / 3.0)

    def test_attack_rate_weights_goals_vs_stronger_opponents(self, eval_date):
        hist = {
            "TeamA": [
                make_record("2024-01-01", "TeamA", "Weak", 3, 0, away_elo=1200.0),
                make_record("2024-02-01", "TeamA", "Weak", 3, 0, away_elo=1200.0),
                make_record("2024-03-01", "TeamA", "Weak", 3, 0, away_elo=1200.0),
                make_record("2024-04-01", "TeamA", "Weak", 3, 0, away_elo=1200.0),
                make_record("2024-05-01", "TeamA", "Weak", 3, 0, away_elo=1200.0),
                make_record("2024-06-01", "TeamA", "Elite", 3, 0, away_elo=1800.0),
            ]
        }
        attack, _ = _get_rolling_rates(hist["TeamA"], "TeamA", eval_date)
        unweighted, _ = _rolling_rates_from_scored_conceded(
            np.array([3.0, 3.0, 3.0, 3.0, 3.0, 3.0]),
            np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        )
        assert attack > unweighted

    def test_defense_rate_conceding_to_elite_hurts_less(self, eval_date):
        # Same 4 goals conceded total; blowout vs elite penalized less than vs minnow
        bad_loss_to_elite = {
            "TeamA": [
                make_record("2024-01-01", "Elite", "TeamA", 4, 0, home_elo=1800.0),
                make_record("2024-02-01", "Minnow", "TeamA", 0, 0, home_elo=1200.0),
                make_record("2024-03-01", "Minnow", "TeamA", 0, 0, home_elo=1200.0),
                make_record("2024-04-01", "Minnow", "TeamA", 0, 0, home_elo=1200.0),
                make_record("2024-05-01", "Minnow", "TeamA", 0, 0, home_elo=1200.0),
            ]
        }
        bad_loss_to_minnow = {
            "TeamA": [
                make_record("2024-01-01", "Minnow", "TeamA", 4, 0, home_elo=1200.0),
                make_record("2024-02-01", "Elite", "TeamA", 0, 0, home_elo=1800.0),
                make_record("2024-03-01", "Elite", "TeamA", 0, 0, home_elo=1800.0),
                make_record("2024-04-01", "Elite", "TeamA", 0, 0, home_elo=1800.0),
                make_record("2024-05-01", "Elite", "TeamA", 0, 0, home_elo=1800.0),
            ]
        }
        _, defense_elite_loss = _get_rolling_rates(
            bad_loss_to_elite["TeamA"], "TeamA", eval_date
        )
        _, defense_minnow_loss = _get_rolling_rates(
            bad_loss_to_minnow["TeamA"], "TeamA", eval_date
        )
        assert defense_elite_loss > defense_minnow_loss
