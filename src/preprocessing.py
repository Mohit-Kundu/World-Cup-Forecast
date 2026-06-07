"""
src/preprocessing.py
====================
Data loading, cleaning, and team history chain construction.

Pipeline:
  1. Load history_stat.csv, elo.csv, former_names.csv
  2. Standardise team names across datasets
  3. Merge Elo ratings onto each match row
  4. Build per-team chronological MatchRecord chains

Public API:
  load_and_preprocess(data_dir) -> (df_matches, team_hist, elo_lookup)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.helpers import MatchRecord

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Team Name Standardisation
# ---------------------------------------------------------------------------

# Manual alias overrides (applied after former_names.csv lookup)
TEAM_ALIASES: Dict[str, str] = {
    "USA": "United States",
    "US": "United States",
    "U.S.A.": "United States",
    "Czech Republic": "Czechia",
    "Republic of Ireland": "Ireland",
    "Northern Ireland": "Northern Ireland",  # keep separate
    "Korea Republic": "South Korea",
    "Korea DPR": "North Korea",
    "IR Iran": "Iran",
    "Chinese Taipei": "Taiwan",
    "Kyrgyz Republic": "Kyrgyzstan",
    "Bosnia and Herzegovina": "Bosnia & Herzegovina",
    "China PR": "China",
    "UAE": "United Arab Emirates",
    "North Macedonia": "North Macedonia",
    "Cote d'Ivoire": "Ivory Coast",
    "Congo DR": "DR Congo",
    "Cape Verde Islands": "Cape Verde",
    # WC 2026 playoff placeholders
    "UEFA Playoff A": "Ukraine",
    "UEFA Playoff B": "Poland",
    "CONCACAF Playoff": "Honduras",
    "OFC Playoff": "New Zealand",
    "CONMEBOL Playoff": "Ecuador",
    "AFC Playoff": "Uzbekistan",
    "CAF Playoff": "Algeria",
    "Inter-confederation playoff 1": "Norway",
    "Inter-confederation playoff 2": "Ivory Coast",
}


def _load_former_names(data_dir: Path) -> Dict[str, str]:
    """
    Loads the former_names.csv file and builds a former->current name mapping.
    Handles both column naming conventions:
      - 'former_name' / 'current_name'
      - 'former' / 'current'
    Falls back to empty dict if file not found.
    """
    path = data_dir / "former_names.csv"
    if not path.exists():
        logger.warning("former_names.csv not found — skipping historical alias mapping.")
        return {}

    df = pd.read_csv(path)
    cols = df.columns.str.lower().str.strip().tolist()

    # Detect column naming convention
    if "former_name" in cols and "current_name" in cols:
        former_col, current_col = "former_name", "current_name"
    elif "former" in cols and "current" in cols:
        former_col, current_col = "former", "current"
    else:
        logger.warning(f"former_names.csv has unrecognised columns {df.columns.tolist()} — skipping.")
        return {}

    df.columns = df.columns.str.lower().str.strip()
    mapping = dict(zip(df[former_col], df[current_col]))
    logger.info(f"Loaded {len(mapping)} historical name aliases.")
    return mapping


def standardise_name(name: str, former_map: Dict[str, str]) -> str:
    """
    Resolves a team name to its canonical WC 2026 version.
    Lookup order: TEAM_ALIASES > former_names.csv > original
    """
    name = str(name).strip()
    if name in TEAM_ALIASES:
        return TEAM_ALIASES[name]
    if name in former_map:
        return former_map[name]
    return name


# ---------------------------------------------------------------------------
# ELO Loader
# ---------------------------------------------------------------------------


def load_elo(data_dir: Path, former_map: Dict[str, str]) -> Dict[str, float]:
    """
    Loads elo.csv and returns a team -> Elo rating dictionary.

    Handles two formats:
      - Time-series: columns [team/Team, date, elo/Elo]
      - Static snapshot: columns [Team, Elo]  (no date column)
    """
    path = data_dir / "elo.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()  # preserve original case first

    # Normalise column names to lowercase
    lower_cols = {c: c.lower() for c in df.columns}
    df = df.rename(columns=lower_cols)

    # Detect Elo column (could be 'elo', 'rating', 'score')
    elo_col = next(
        (c for c in df.columns if "elo" in c or "rating" in c),
        None,
    )
    # Detect team column
    team_col = next(
        (c for c in df.columns if c in ("team", "country", "nation", "team_name")),
        None,
    )

    if elo_col is None:
        raise ValueError(f"Could not find an Elo rating column in elo.csv. Columns: {df.columns.tolist()}")
    if team_col is None:
        raise ValueError(f"Could not find a team name column in elo.csv. Columns: {df.columns.tolist()}")

    # Build team -> elo dict (if time-series, use most recent row per team)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        df = df.groupby(team_col).last().reset_index()

    elo_dict: Dict[str, float] = {}
    for _, row in df.iterrows():
        name = standardise_name(str(row[team_col]), former_map)
        elo_dict[name] = float(row[elo_col])

    logger.info(f"Loaded Elo ratings for {len(elo_dict)} teams.")
    return elo_dict


def get_elo_for_team(
    elo_dict: Dict[str, float], team: str, date: Optional[pd.Timestamp] = None
) -> float:
    """
    Returns the Elo rating for a team. Falls back to 1500.0 if not found.
    The `date` parameter is kept for API compatibility but not used for static snapshots.
    """
    return elo_dict.get(team, 1500.0)


# ---------------------------------------------------------------------------
# History Loader
# ---------------------------------------------------------------------------


def load_history(data_dir: Path, former_map: Dict[str, str]) -> pd.DataFrame:
    """
    Loads and cleans history_stat.csv.

    Expected columns: date, home_team, away_team, home_score, away_score,
                      tournament, neutral (bool)
    """
    path = data_dir / "history_stat.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    df = pd.read_csv(path, parse_dates=["date"])
    df.columns = df.columns.str.lower().str.strip()

    # Normalise column name variants
    rename = {
        "home_score": "home_score",
        "away_score": "away_score",
        "home_goals": "home_score",
        "away_goals": "away_score",
        "home_result": "home_score",
        "away_result": "away_score",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    # Ensure required columns
    required = ["date", "home_team", "away_team", "home_score", "away_score"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"history_stat.csv missing columns: {missing}")

    # Fill optional columns
    if "tournament" not in df.columns:
        df["tournament"] = "Friendly"
    if "neutral" not in df.columns:
        df["neutral"] = False

    # Drop rows with missing scores
    df = df.dropna(subset=["home_score", "away_score"])
    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)

    # Standardise team names
    df["home_team"] = df["home_team"].apply(lambda x: standardise_name(x, former_map))
    df["away_team"] = df["away_team"].apply(lambda x: standardise_name(x, former_map))

    df = df.sort_values("date").reset_index(drop=True)
    logger.info(f"Loaded {len(df):,} historical matches (from {df['date'].min().year} to {df['date'].max().year})")
    return df


# ---------------------------------------------------------------------------
# Team History Chain Builder
# ---------------------------------------------------------------------------


def build_team_history(
    df: pd.DataFrame, elo_dict: Dict[str, float]
) -> Dict[str, List[MatchRecord]]:
    """
    Constructs per-team chronological chains of MatchRecord objects.

    Parameters
    ----------
    df         : cleaned history DataFrame
    elo_dict   : team -> Elo rating dict

    Returns
    -------
    dict mapping team_name -> list[MatchRecord] (sorted by date ascending)
    """
    team_hist: Dict[str, List[MatchRecord]] = {}

    for _, row in df.iterrows():
        home_elo = get_elo_for_team(elo_dict, row["home_team"])
        away_elo = get_elo_for_team(elo_dict, row["away_team"])

        record = MatchRecord(
            date=row["date"],
            home_team=row["home_team"],
            away_team=row["away_team"],
            home_score=int(row["home_score"]),
            away_score=int(row["away_score"]),
            tournament=row["tournament"],
            neutral=bool(row["neutral"]),
            home_elo=home_elo,
            away_elo=away_elo,
        )

        for team in [row["home_team"], row["away_team"]]:
            if team not in team_hist:
                team_hist[team] = []
            team_hist[team].append(record)

    # Sort each team's history by date
    for team in team_hist:
        team_hist[team].sort(key=lambda r: r.date)

    logger.info(f"Built history chains for {len(team_hist)} teams.")
    return team_hist


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_and_preprocess(
    data_dir: str | Path,
) -> Tuple[pd.DataFrame, Dict[str, List[MatchRecord]], Dict[str, float]]:
    """
    Full preprocessing pipeline. Loads all raw data, standardises names,
    attaches Elo ratings, and constructs team history chains.

    Parameters
    ----------
    data_dir : path to the data/ directory

    Returns
    -------
    df_matches  : cleaned match DataFrame with Elo columns attached
    team_hist   : dict[team_name -> list[MatchRecord]]
    elo_dict    : dict[team_name -> Elo rating] for simulation-time lookup
    """
    data_dir = Path(data_dir)
    former_map = _load_former_names(data_dir)

    elo_dict = load_elo(data_dir, former_map)
    df_matches = load_history(data_dir, former_map)

    # Attach Elo ratings to each match row (vectorised lookup)
    logger.info("Attaching Elo ratings to match history...")
    df_matches["home_elo"] = df_matches["home_team"].map(
        lambda t: elo_dict.get(t, 1500.0)
    )
    df_matches["away_elo"] = df_matches["away_team"].map(
        lambda t: elo_dict.get(t, 1500.0)
    )

    team_hist = build_team_history(df_matches, elo_dict)
    return df_matches, team_hist, elo_dict
