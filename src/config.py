"""
src/config.py
==============
Centralized configuration settings and constants for the FIFA WC 2026 prediction pipeline.
"""

from typing import Dict, List
import pandas as pd

# Global reproducibility seed
RANDOM_SEED = 42

# Tournament configuration
TOURNAMENT_DATE = pd.Timestamp("2026-06-11")
HOST_NATIONS = {"United States", "Canada", "Mexico"}

# Tournament importance weights (used in feature engineering)
TOURNAMENT_WEIGHTS: Dict[str, float] = {
    "FIFA World Cup": 1.30,
    "UEFA Euro": 1.20,
    "Copa America": 1.20,
    "Africa Cup of Nations": 1.15,
    "Asian Cup": 1.15,
    "CONCACAF Gold Cup": 1.10,
    "Copa del Pacifico": 1.05,
    "Friendly": 1.00,
}

# Official FIFA WC 2026 Groups
WC2026_GROUPS: Dict[str, List[str]] = {
    "A": ["United States", "Panama", "Bolivia", "Morocco"],
    "B": ["Argentina", "Chile", "Peru", "Australia"],
    "C": ["Mexico", "Jamaica", "Venezuela", "Paraguay"],
    "D": ["Brazil", "Ecuador", "Egypt", "Serbia"],
    "E": ["Spain", "Uruguay", "Uzbekistan", "South Korea"],
    "F": ["France", "Belgium", "Croatia", "South Africa"],
    "G": ["England", "Senegal", "Colombia", "Tunisia"],
    "H": ["Portugal", "Algeria", "Cameroon", "Honduras"],
    "I": ["Germany", "Japan", "Iran", "Saudi Arabia"],
    "J": ["Netherlands", "Nigeria", "New Zealand", "Ivory Coast"],
    "K": ["Italy", "Slovenia", "Qatar", "Ukraine"],
    "L": ["Canada", "Switzerland", "Norway", "Poland"],
}

# Machine learning model feature columns (single source of truth)
FEATURE_COLS = [
    "elo_diff",
    "home_elo",
    "away_elo",
    "home_attack",
    "home_defense",
    "away_attack",
    "away_defense",
    "tournament_weight",
    "is_host",
    "home_recent_form",
    "away_recent_form",
    "h2h_win_rate",
    "h2h_goal_diff",
    "home_discipline",
    "away_discipline",
]

# Model training parameters
MIN_TRAIN_SAMPLES = 100

# Monte Carlo match/penalty simulation parameters
EXTRA_TIME_GOALS_EXPECTED = 0.8
PENALTY_ELO_SCALE = 400.0
PENALTY_PROB_MIN = 0.35
PENALTY_PROB_MAX = 0.65
