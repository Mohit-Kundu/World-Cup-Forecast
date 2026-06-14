"""Tests for predictions JSON serialization and loading."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from src.predictions_io import (
    format_predictions_response,
    load_predictions_json,
    predictions_json_path,
    save_predictions_json,
)
from src.wrapped_awards import build_wrapped_awards


def _minimal_mc_output() -> dict:
    return {
        "match_results": {
            1: {
                "home_team": "Mexico",
                "away_team": "South Africa",
                "stage": "Group",
                "most_common_home_goals": 1,
                "most_common_away_goals": 0,
                "home_win_prob": 0.69,
                "draw_prob": 0.20,
                "away_win_prob": 0.11,
            }
        },
        "champion_probs": {"Spain": 0.21, "Argentina": 0.12},
        "finalist_probs": {"Spain": 0.32, "Argentina": 0.19},
        "qualify_probs": {"Mexico": 0.85},
        "r32_probs": {"Spain": 0.90},
        "r16_probs": {"Spain": 0.75},
        "qf_probs": {"Spain": 0.55},
        "sf_probs": {"Spain": 0.40},
        "group_standings": {
            "A": [
                {
                    "team": "Mexico",
                    "rank": 1,
                    "pts": 7,
                    "gd": 3,
                    "gf": 4,
                    "played": 3,
                    "qualify_prob": 0.85,
                }
            ]
        },
        "predicted_final": {
            "home_team": "Spain",
            "away_team": "Argentina",
            "winner": "Spain",
            "runner_up": "Argentina",
            "pairing_prob": 0.08,
            "winner_prob": 0.62,
        },
        "team_upset_counts": {"Morocco": 41},
    }


def _minimal_team_stats() -> dict:
    return {
        "Mexico": {
            "FIFA ELO Rating": "1800",
            "Recent Form (W5)": "60.0%",
            "Attack Strength (Avg Goals)": "1.50",
            "Defense Rating (Inverse)": "1.20",
            "Expected Conceded Goals": "0.83",
            "Rolling Attack Rate": "1.45",
            "Rolling Conceded Rate": "0.83",
            "ELO-Adjusted Attack Score": "1.200",
            "ELO-Adjusted Fortress Score": "0.900",
            "Rolling Match Count": "8",
            "Avg Opponent ELO (Rolling)": "1700",
            "Last 5 Goals Scored": "6",
            "Discipline Index (Expected Cards)": "1.10",
        }
    }


def test_format_predictions_response_converts_numpy_scalars():
    mc = _minimal_mc_output()
    mc["match_results"][1]["most_common_home_goals"] = np.int32(1)
    mc["match_results"][1]["most_common_away_goals"] = np.int32(0)
    mc["group_standings"]["A"][0]["rank"] = np.int32(1)

    payload = format_predictions_response(
        mc, _minimal_team_stats(), n_simulations=100
    )

    assert type(payload["match_results"]["1"]["most_common_home_goals"]) is int
    assert type(payload["group_standings"]["A"][0]["rank"]) is int


def test_format_predictions_response_stringifies_match_keys():
    payload = format_predictions_response(
        _minimal_mc_output(), _minimal_team_stats(), n_simulations=100
    )

    assert "1" in payload["match_results"]
    assert 1 not in payload["match_results"]
    assert payload["match_results"]["1"]["home_team"] == "Mexico"
    assert payload["n_simulations"] == 100
    assert payload["champion_probs"]["Spain"] == pytest.approx(0.21)
    assert payload["predicted_final"]["winner"] == "Spain"


def test_save_and_load_predictions_json_roundtrip(tmp_path: Path):
    payload = format_predictions_response(
        _minimal_mc_output(), _minimal_team_stats(), n_simulations=500
    )

    saved_path = save_predictions_json(payload, tmp_path)
    assert saved_path == predictions_json_path(tmp_path)
    assert saved_path.is_file()

    loaded = load_predictions_json(tmp_path)
    assert loaded is not None
    assert loaded["n_simulations"] == 500
    assert loaded["match_results"]["1"]["away_team"] == "South Africa"
    assert loaded["group_standings"]["A"][0]["team"] == "Mexico"


def test_format_predictions_response_includes_wrapped_awards():
    payload = format_predictions_response(
        _minimal_mc_output(), _minimal_team_stats(), n_simulations=100
    )

    assert "wrapped_awards" in payload
    assert isinstance(payload["wrapped_awards"], list)
    assert payload["wrapped_awards"] == build_wrapped_awards(
        _minimal_mc_output(), _minimal_team_stats(), 100
    )


def test_load_predictions_json_missing_file(tmp_path: Path):
    assert load_predictions_json(tmp_path) is None


def test_load_predictions_json_corrupt_file(tmp_path: Path):
    path = predictions_json_path(tmp_path)
    path.write_text("{ not valid json", encoding="utf-8")

    assert load_predictions_json(tmp_path) is None
