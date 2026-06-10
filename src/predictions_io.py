"""
src/predictions_io.py
=====================
Serialize and load the full dashboard prediction payload for the React UI.
Shared by main.py (write) and backend/api.py (read).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from src.config import PREDICTIONS_JSON, TOURNAMENT_DATE, WC2026_GROUPS
from src.feature_engineering import (
    _get_rolling_rates,
    build_team_history_dfs,
    compute_dynamic_discipline,
    get_team_form,
)

logger = logging.getLogger(__name__)


def _to_json_safe(value: Any) -> Any:
    """Recursively convert numpy scalars to native Python types for JSON."""
    if isinstance(value, dict):
        return {str(k): _to_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_json_safe(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def predictions_json_path(output_dir: str | Path) -> Path:
    """Return the path to the pipeline predictions snapshot."""
    return Path(output_dir) / PREDICTIONS_JSON


def build_team_stats(team_hist: dict, elo_dict: dict) -> Dict[str, Dict[str, str]]:
    """Calculate team base statistics for all WC 2026 participants."""
    team_dfs = build_team_history_dfs(team_hist)
    stats: Dict[str, Dict[str, str]] = {}

    for _group, teams in WC2026_GROUPS.items():
        for team in teams:
            elo = elo_dict.get(team, 1500.0)
            history = team_hist.get(team, [])
            team_df = team_dfs.get(team)
            attack, defense = _get_rolling_rates(
                history, team, TOURNAMENT_DATE, team_df=team_df
            )
            form = get_team_form(
                team_hist, team, TOURNAMENT_DATE, team_dfs=team_dfs
            )
            discipline = compute_dynamic_discipline(
                team_hist, team, TOURNAMENT_DATE, team_dfs=team_dfs
            )

            stats[team] = {
                "FIFA ELO Rating": f"{int(round(elo))}",
                "Recent Form (W5)": f"{form:.1%}",
                "Attack Strength (Avg Goals)": f"{attack:.2f}",
                "Defense Rating (Inverse)": f"{defense:.2f}",
                "Expected Conceded Goals": f"{1.0 / max(defense, 0.1):.2f}",
                "Discipline Index (Expected Cards)": f"{discipline:.2f}",
            }

    return stats


def format_predictions_response(
    mc_output: dict,
    team_stats: dict,
    n_simulations: int,
) -> dict:
    """Serialize Monte Carlo results for the frontend API."""
    match_results = {}
    for match_id, result in mc_output["match_results"].items():
        match_results[str(match_id)] = {
            "home_team": result["home_team"],
            "away_team": result["away_team"],
            "stage": result["stage"],
            "most_common_home_goals": result["most_common_home_goals"],
            "most_common_away_goals": result["most_common_away_goals"],
            "home_win_prob": result["home_win_prob"],
            "draw_prob": result["draw_prob"],
            "away_win_prob": result["away_win_prob"],
        }

    return _to_json_safe(
        {
            "match_results": match_results,
            "champion_probs": mc_output["champion_probs"],
            "finalist_probs": mc_output["finalist_probs"],
            "qualify_probs": mc_output.get("qualify_probs", {}),
            "r32_probs": mc_output.get("r32_probs", {}),
            "r16_probs": mc_output.get("r16_probs", {}),
            "qf_probs": mc_output.get("qf_probs", {}),
            "sf_probs": mc_output.get("sf_probs", {}),
            "group_standings": mc_output.get("group_standings", {}),
            "predicted_final": mc_output.get(
                "predicted_final",
                {
                    "home_team": "",
                    "away_team": "",
                    "winner": "",
                    "runner_up": "",
                    "pairing_prob": 0.0,
                    "winner_prob": 0.0,
                },
            ),
            "team_stats": team_stats,
            "n_simulations": n_simulations,
        }
    )


def save_predictions_json(payload: dict, output_dir: str | Path) -> Path:
    """Write the dashboard payload to output/predictions.json."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = predictions_json_path(output_dir)
    with path.open("w", encoding="utf-8") as f:
        json.dump(_to_json_safe(payload), f, indent=2)
    return path


def load_predictions_json(output_dir: str | Path) -> Optional[Dict[str, Any]]:
    """Load pipeline snapshot if present; return None on missing or corrupt file."""
    path = predictions_json_path(output_dir)
    if not path.is_file():
        return None

    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not load %s: %s", path, exc)
        return None
