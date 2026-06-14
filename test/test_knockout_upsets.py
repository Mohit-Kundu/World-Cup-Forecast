"""Tests for knockout upset counting used by giant-killer awards."""

from __future__ import annotations

from src.knockout_engine import _count_knockout_upsets


def test_count_knockout_upsets_tracks_lower_elo_winner():
    results = [
        {
            "stage": "Round of 16",
            "home_team": "Spain",
            "away_team": "Morocco",
            "winner": "Morocco",
        },
        {
            "stage": "Quarter-Final",
            "home_team": "France",
            "away_team": "Morocco",
            "winner": "France",
        },
    ]
    elo = {"Spain": 2100.0, "Morocco": 1780.0, "France": 2050.0}

    upsets = _count_knockout_upsets(results, elo)

    assert upsets["Morocco"] == 1
    assert upsets["France"] == 0
