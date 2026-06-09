"""Tests for performance-related pipeline changes."""

from __future__ import annotations

import numpy as np

from src.cache_utils import compute_data_fingerprint
from src.feature_engineering import _append_training_targets
from src.helpers import resolve_group_standings


def test_corners_targets_are_deterministic():
    row = {
        "home_score": 2,
        "away_score": 1,
        "date": "2024-01-01",
    }
    feats = {
        "home_attack": 1.5,
        "away_defense": 0.8,
        "away_attack": 1.1,
        "home_defense": 0.9,
        "home_discipline": 2.0,
        "away_discipline": 2.5,
    }
    out1 = _append_training_targets(dict(feats), row)
    out2 = _append_training_targets(dict(feats), row)
    assert out1["home_corners"] == out2["home_corners"]
    assert out1["away_corners"] == out2["away_corners"]


def test_resolve_group_standings_seeded_rng():
    results = [
        {
            "home_team": "A",
            "away_team": "B",
            "home_goals": 1,
            "away_goals": 1,
            "home_yellow": 1,
            "away_yellow": 1,
            "home_red": 0,
            "away_red": 0,
        },
        {
            "home_team": "C",
            "away_team": "D",
            "home_goals": 0,
            "away_goals": 0,
            "home_yellow": 0,
            "away_yellow": 0,
            "home_red": 0,
            "away_red": 0,
        },
        {
            "home_team": "A",
            "away_team": "C",
            "home_goals": 0,
            "away_goals": 0,
            "home_yellow": 0,
            "away_yellow": 0,
            "home_red": 0,
            "away_red": 0,
        },
        {
            "home_team": "B",
            "away_team": "D",
            "home_goals": 0,
            "away_goals": 0,
            "home_yellow": 0,
            "away_yellow": 0,
            "home_red": 0,
            "away_red": 0,
        },
        {
            "home_team": "A",
            "away_team": "D",
            "home_goals": 0,
            "away_goals": 0,
            "home_yellow": 0,
            "away_yellow": 0,
            "home_red": 0,
            "away_red": 0,
        },
        {
            "home_team": "B",
            "away_team": "C",
            "home_goals": 0,
            "away_goals": 0,
            "home_yellow": 0,
            "away_yellow": 0,
            "home_red": 0,
            "away_red": 0,
        },
    ]
    rng1 = np.random.default_rng(99)
    rng2 = np.random.default_rng(99)
    df1 = resolve_group_standings(results, rng=rng1)
    df2 = resolve_group_standings(results, rng=rng2)
    assert df1["team"].tolist() == df2["team"].tolist()


def test_data_fingerprint_stable_for_same_dir(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "history_stat.csv").write_text("a", encoding="utf-8")
    (data_dir / "elo.csv").write_text("b", encoding="utf-8")
    fp1 = compute_data_fingerprint(data_dir)
    fp2 = compute_data_fingerprint(data_dir)
    assert fp1 == fp2
