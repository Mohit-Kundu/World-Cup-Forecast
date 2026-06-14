"""Tests for wrapped award card computation."""

from __future__ import annotations

import pytest

from src.wrapped_awards import build_wrapped_awards


def _sample_team_stats() -> dict:
    return {
        "Japan": {
            "FIFA ELO Rating": "1820",
            "Recent Form (W5)": "60.0%",
            "Attack Strength (Avg Goals)": "1.70",
            "Defense Rating (Inverse)": "1.10",
            "Expected Conceded Goals": "0.91",
            "Discipline Index (Expected Cards)": "1.00",
        },
        "Morocco": {
            "FIFA ELO Rating": "1780",
            "Recent Form (W5)": "55.0%",
            "Attack Strength (Avg Goals)": "1.40",
            "Defense Rating (Inverse)": "1.05",
            "Expected Conceded Goals": "0.95",
            "Discipline Index (Expected Cards)": "1.10",
        },
        "Spain": {
            "FIFA ELO Rating": "2165",
            "Recent Form (W5)": "70.0%",
            "Attack Strength (Avg Goals)": "2.89",
            "Defense Rating (Inverse)": "1.40",
            "Expected Conceded Goals": "0.64",
            "Rolling Attack Rate": "3.10",
            "Rolling Conceded Rate": "0.64",
            "ELO-Adjusted Attack Score": "3.254",
            "ELO-Adjusted Fortress Score": "0.520",
            "Rolling Match Count": "10",
            "Avg Opponent ELO (Rolling)": "1820",
            "Last 5 Goals Scored": "14",
            "Discipline Index (Expected Cards)": "0.90",
        },
        "France": {
            "FIFA ELO Rating": "2050",
            "Recent Form (W5)": "65.0%",
            "Attack Strength (Avg Goals)": "2.10",
            "Defense Rating (Inverse)": "1.50",
            "Expected Conceded Goals": "0.67",
            "Rolling Attack Rate": "2.10",
            "Rolling Conceded Rate": "0.67",
            "ELO-Adjusted Attack Score": "2.150",
            "ELO-Adjusted Fortress Score": "0.540",
            "Rolling Match Count": "10",
            "Avg Opponent ELO (Rolling)": "1810",
            "Last 5 Goals Scored": "8",
            "Discipline Index (Expected Cards)": "1.00",
        },
        "Netherlands": {
            "FIFA ELO Rating": "1980",
            "Recent Form (W5)": "58.0%",
            "Attack Strength (Avg Goals)": "1.90",
            "Defense Rating (Inverse)": "1.20",
            "Expected Conceded Goals": "0.83",
            "Discipline Index (Expected Cards)": "1.05",
        },
        "Sweden": {
            "FIFA ELO Rating": "1900",
            "Recent Form (W5)": "52.0%",
            "Attack Strength (Avg Goals)": "1.60",
            "Defense Rating (Inverse)": "1.15",
            "Expected Conceded Goals": "0.87",
            "Discipline Index (Expected Cards)": "1.00",
        },
        "Tunisia": {
            "FIFA ELO Rating": "1700",
            "Recent Form (W5)": "48.0%",
            "Attack Strength (Avg Goals)": "1.20",
            "Defense Rating (Inverse)": "1.00",
            "Expected Conceded Goals": "1.00",
            "Discipline Index (Expected Cards)": "1.20",
        },
        "Paraguay": {
            "FIFA ELO Rating": "1750",
            "Recent Form (W5)": "50.0%",
            "Attack Strength (Avg Goals)": "1.30",
            "Defense Rating (Inverse)": "1.00",
            "Expected Conceded Goals": "1.00",
            "Discipline Index (Expected Cards)": "1.10",
        },
        "United States": {
            "FIFA ELO Rating": "1850",
            "Recent Form (W5)": "54.0%",
            "Attack Strength (Avg Goals)": "1.50",
            "Defense Rating (Inverse)": "1.05",
            "Expected Conceded Goals": "0.95",
            "Discipline Index (Expected Cards)": "1.00",
        },
        "Australia": {
            "FIFA ELO Rating": "1720",
            "Recent Form (W5)": "46.0%",
            "Attack Strength (Avg Goals)": "1.25",
            "Defense Rating (Inverse)": "0.95",
            "Expected Conceded Goals": "1.05",
            "Discipline Index (Expected Cards)": "1.15",
        },
        "Türkiye": {
            "FIFA ELO Rating": "1800",
            "Recent Form (W5)": "57.0%",
            "Attack Strength (Avg Goals)": "1.45",
            "Defense Rating (Inverse)": "1.02",
            "Expected Conceded Goals": "0.98",
            "Discipline Index (Expected Cards)": "1.05",
        },
    }


def _sample_mc_output() -> dict:
    return {
        "champion_probs": {
            "Japan": 0.031,
            "Spain": 0.210,
            "France": 0.180,
            "Morocco": 0.005,
        },
        "qualify_probs": {
            "Japan": 0.92,
            "Netherlands": 0.88,
            "Sweden": 0.15,
            "Tunisia": 0.12,
            "Paraguay": 0.30,
            "United States": 0.75,
            "Australia": 0.40,
            "Türkiye": 0.70,
        },
        "group_standings": {
            "D": [
                {
                    "team": "Paraguay",
                    "rank": 1,
                    "pts": 7,
                    "gd": 2,
                    "gf": 4,
                    "played": 3,
                    "qualify_prob": 0.30,
                },
                {
                    "team": "United States",
                    "rank": 2,
                    "pts": 6,
                    "gd": 1,
                    "gf": 3,
                    "played": 3,
                    "qualify_prob": 0.75,
                },
                {
                    "team": "Türkiye",
                    "rank": 3,
                    "pts": 4,
                    "gd": 0,
                    "gf": 2,
                    "played": 3,
                    "qualify_prob": 0.70,
                },
                {
                    "team": "Australia",
                    "rank": 4,
                    "pts": 1,
                    "gd": -3,
                    "gf": 1,
                    "played": 3,
                    "qualify_prob": 0.55,
                },
            ]
        },
        "team_upset_counts": {
            "Morocco": 410,
            "Japan": 120,
        },
    }


def test_build_wrapped_awards_returns_six_cards_with_expected_ids():
    awards = build_wrapped_awards(_sample_mc_output(), _sample_team_stats(), 1000)

    assert len(awards) == 6
    assert sorted(card["id"] for card in awards) == sorted([
        "group-of-death",
        "group-of-chaos",
        "dark-horse",
        "lethal-attack",
        "fortress",
        "giant-killer",
    ])


def test_build_wrapped_awards_selects_expected_winners():
    awards = build_wrapped_awards(_sample_mc_output(), _sample_team_stats(), 1000)
    by_id = {card["id"]: card for card in awards}

    assert by_id["giant-killer"]["teams"] == ["Morocco"]
    assert by_id["giant-killer"]["bigNumber"] == "0.4"
    assert by_id["lethal-attack"]["teams"] == ["Spain"]
    assert by_id["lethal-attack"]["bigNumber"] == "3.10"
    assert by_id["fortress"]["teams"] == ["Spain"]
    assert by_id["fortress"]["bigNumber"] == "0.64"
    assert by_id["group-of-chaos"]["badgeLabel"] == "Group D"
    assert by_id["group-of-chaos"]["statLabel"] == "qualification entropy"
    assert by_id["group-of-chaos"]["bigNumber"] == "1.32"


def test_group_of_chaos_uses_shannon_entropy():
    from src.wrapped_awards import _build_group_of_chaos

    qualify_probs = {
        "United States": 0.457,
        "Paraguay": 0.539,
        "Australia": 0.392,
        "Türkiye": 0.611,
        "Spain": 0.989,
        "Uruguay": 0.792,
        "Saudi Arabia": 0.105,
        "Cape Verde": 0.114,
    }

    card = _build_group_of_chaos(qualify_probs, {})

    assert card["badgeLabel"] == "Group D"
    assert float(card["bigNumber"]) == pytest.approx(1.37, abs=0.02)
    assert "favorite" in card["insight"].lower()


def test_group_of_death_uses_top3_average_elo():
    from src.wrapped_awards import _build_group_of_death

    team_stats = {
        "France": {"FIFA ELO Rating": "2081"},
        "Senegal": {"FIFA ELO Rating": "1878"},
        "Norway": {"FIFA ELO Rating": "1912"},
        "Iraq": {"FIFA ELO Rating": "1607"},
        "United States": {"FIFA ELO Rating": "1721"},
        "Paraguay": {"FIFA ELO Rating": "1833"},
        "Australia": {"FIFA ELO Rating": "1783"},
        "Türkiye": {"FIFA ELO Rating": "1902"},
    }

    card = _build_group_of_death(team_stats)

    assert card["badgeLabel"] == "Group I"
    assert card["bigNumber"] == "1957"
    assert card["statLabel"] == "avg. ELO of top 3 teams"
    assert card["teams"] == ["France", "Senegal", "Norway", "Iraq"]
    assert card["insight"] == "Top 3: France, Norway, Senegal with an average ELO of 1957."


def test_build_wrapped_awards_card_shape():
    awards = build_wrapped_awards(_sample_mc_output(), _sample_team_stats(), 1000)

    for card in awards:
        assert isinstance(card["id"], str)
        assert isinstance(card["bigNumber"], str)
        assert isinstance(card["statLabel"], str)
        assert isinstance(card["teams"], list)
        assert isinstance(card["insight"], str)
