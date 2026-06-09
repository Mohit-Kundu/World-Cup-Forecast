"""Unit tests for standings, bracket, and aggregation helper calculations."""

from __future__ import annotations

from collections import Counter
from unittest.mock import patch

import pandas as pd
import pytest

from src.config import WC2026_GROUPS
from src.helpers import (
    get_group_fixtures,
    resolve_group_standings,
    build_knockout_bracket,
    build_predicted_group_standings,
    build_predicted_final,
    format_submission,
)


def _match(
    home: str,
    away: str,
    hg: int,
    ag: int,
    home_yellow: int = 0,
    away_yellow: int = 0,
    home_red: int = 0,
    away_red: int = 0,
) -> dict:
    return {
        "home_team": home,
        "away_team": away,
        "home_goals": hg,
        "away_goals": ag,
        "home_yellow": home_yellow,
        "away_yellow": away_yellow,
        "home_red": home_red,
        "away_red": away_red,
    }


class TestGroupFixtures:
    def test_fixture_count(self):
        fixtures = get_group_fixtures()
        assert len(fixtures) == 72
        assert fixtures[0]["match_id"] == 1
        assert fixtures[-1]["match_id"] == 72

    def test_each_group_has_six_round_robin_matches(self):
        fixtures = get_group_fixtures()
        for group in WC2026_GROUPS:
            group_fixtures = [f for f in fixtures if f["group"] == group]
            assert len(group_fixtures) == 6
            teams = set()
            for f in group_fixtures:
                teams.add(f["home_team"])
                teams.add(f["away_team"])
            assert teams == set(WC2026_GROUPS[group])


class TestResolveGroupStandings:
    def test_three_team_points_and_goal_difference(self):
        results = [
            _match("TeamA", "TeamB", 2, 0),
            _match("TeamA", "TeamC", 1, 1),
            _match("TeamB", "TeamC", 0, 1),
        ]
        standings = resolve_group_standings(results)

        by_team = {row["team"]: row for _, row in standings.iterrows()}
        assert by_team["TeamA"]["pts"] == 4
        assert by_team["TeamA"]["gd"] == 2
        assert by_team["TeamC"]["pts"] == 4
        assert by_team["TeamC"]["gd"] == 1
        assert by_team["TeamB"]["pts"] == 0

        assert standings.loc[standings["rank"] == 1, "team"].iloc[0] == "TeamA"
        assert standings.loc[standings["rank"] == 2, "team"].iloc[0] == "TeamC"
        assert standings.loc[standings["rank"] == 3, "team"].iloc[0] == "TeamB"

    def test_yellow_card_tiebreaker(self):
        # All three teams: 2 pts, GD 0, GF 2 — separated by yellow cards (ascending)
        results = [
            _match("TeamA", "TeamB", 1, 1, home_yellow=3, away_yellow=1),
            _match("TeamA", "TeamC", 1, 1, home_yellow=0, away_yellow=0),
            _match("TeamB", "TeamC", 1, 1, home_yellow=0, away_yellow=0),
        ]
        with patch("src.helpers.random.random", side_effect=[0.5, 0.5, 0.5]):
            standings = resolve_group_standings(results)

        ranked = standings.sort_values("rank")["team"].tolist()
        assert ranked == ["TeamC", "TeamB", "TeamA"]
        assert standings.loc[standings["team"] == "TeamA", "yellow"].iloc[0] == 3
        assert standings.loc[standings["team"] == "TeamB", "yellow"].iloc[0] == 1
        assert standings.loc[standings["team"] == "TeamC", "yellow"].iloc[0] == 0

    def test_draw_awards_one_point_each(self):
        results = [_match("X", "Y", 2, 2)]
        standings = resolve_group_standings(results)
        assert standings.loc[standings["team"] == "X", "pts"].iloc[0] == 1
        assert standings.loc[standings["team"] == "Y", "pts"].iloc[0] == 1


class TestKnockoutBracket:
    def test_builds_sixteen_r32_matches(self):
        group_standings = {}
        for group, teams in WC2026_GROUPS.items():
            group_standings[group] = pd.DataFrame(
                {
                    "team": teams,
                    "rank": [1, 2, 3, 4],
                    "pts": [9, 6, 3, 0],
                    "gd": [3, 1, -1, -3],
                    "gf": [5, 4, 2, 1],
                    "ga": [2, 3, 3, 4],
                    "yellow": [1, 2, 3, 4],
                    "red": [0, 0, 0, 0],
                    "played": [3, 3, 3, 3],
                    "rand": [0.1, 0.2, 0.3, 0.4],
                }
            )

        bracket = build_knockout_bracket(group_standings)
        assert len(bracket) == 16
        assert bracket[0]["match_id"] == 49
        assert bracket[-1]["match_id"] == 64
        assert bracket[0]["home_team"] == WC2026_GROUPS["A"][0]
        assert bracket[0]["away_team"] == WC2026_GROUPS["B"][1]


class TestPredictedOutputs:
    def test_build_predicted_final(self):
        pairing_counter = Counter({("France", "Brazil"): 7, ("Spain", "Germany"): 3})
        winner_by_pairing = {("France", "Brazil"): Counter({"France": 5, "Brazil": 2})}

        result = build_predicted_final(pairing_counter, winner_by_pairing, 10)
        assert result["home_team"] == "France"
        assert result["away_team"] == "Brazil"
        assert result["winner"] == "France"
        assert result["runner_up"] == "Brazil"
        assert result["pairing_prob"] == pytest.approx(0.7)
        assert result["winner_prob"] == pytest.approx(5 / 7)

    def test_build_predicted_group_standings_uses_mode_scorelines(self):
        mc_results = {
            1: {
                "home_team": "Mexico",
                "away_team": "South Africa",
                "stage": "Group",
                "most_common_home_goals": 2,
                "most_common_away_goals": 0,
                "home_win_prob": 0.8,
                "draw_prob": 0.1,
                "away_win_prob": 0.1,
            },
        }
        qualify_probs = {"Mexico": 0.9, "South Africa": 0.1}
        standings = build_predicted_group_standings(mc_results, qualify_probs)

        group_a = standings["A"]
        mexico = next(r for r in group_a if r["team"] == "Mexico")
        assert mexico["pts"] == 3
        assert mexico["gf"] == 2
        assert mexico["qualify_prob"] == pytest.approx(0.9)

    def test_format_submission_rounds_probabilities(self):
        mc_results = {
            1: {
                "stage": "Group",
                "home_team": "A",
                "away_team": "B",
                "most_common_home_goals": 1,
                "most_common_away_goals": 0,
                "home_win_prob": 0.5123456,
                "draw_prob": 0.2345678,
                "away_win_prob": 0.2530864,
            }
        }
        df = format_submission(mc_results)
        assert df.iloc[0]["home_win_prob"] == 0.5123
        assert df.iloc[0]["predicted_home_goals"] == 1
