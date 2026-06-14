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
    "A": ["Mexico", "South Africa", "South Korea", "Czechia"],
    "B": ["Canada", "Switzerland", "Qatar", "Bosnia and Herzegovina"],
    "C": ["Brazil", "Morocco", "Scotland", "Haiti"],
    "D": ["United States", "Paraguay", "Australia", "Türkiye"],
    "E": ["Germany", "Ecuador", "Ivory Coast", "Curaçao"],
    "F": ["Netherlands", "Sweden", "Japan", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Uruguay", "Saudi Arabia", "Cape Verde"],
    "I": ["France", "Senegal", "Norway", "Iraq"],
    "J": ["Argentina", "Austria", "Algeria", "Jordan"],
    "K": ["Portugal", "Colombia", "Uzbekistan", "DR Congo"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
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
MIN_MATCH_YEAR = 2010  # Earliest match year included in training data
MIN_TRAIN_SAMPLES = 100
LGBM_EARLY_STOPPING_ROUNDS = 50
LGBM_N_JOBS_TRAINING = 2  # per-model threads when fitting models in parallel
TRAIN_MODELS_PARALLEL = True

# Feature matrix disk cache (skip rebuild when data unchanged)
FEATURE_CACHE_DIR = "cache"

# Pipeline output artifacts (CSVs, logs, UI snapshot)
OUTPUT_DIR = "output"
PREDICTIONS_JSON = "predictions.json"

# Monte Carlo parallelism (knockout loop workers; -1 = all cores)
MC_N_JOBS = 2

# Monte Carlo match/penalty simulation parameters
EXTRA_TIME_GOALS_EXPECTED = 0.8
PENALTY_ELO_SCALE = 400.0
PENALTY_PROB_MIN = 0.35
PENALTY_PROB_MAX = 0.65

# Bayesian smoothing for wrapped award attack/defense rates
ROLLING_RATE_WINDOW = 10
BAYESIAN_SMOOTHING_WEIGHT = 5
BAYESIAN_DEFAULT_AVG_GOALS = 1.25
BAYESIAN_DEFAULT_AVG_CONCEDED = 1.10

# Monte Carlo iteration counts
N_SIMULATIONS_DEFAULT = 15_500  # main.py CLI + run_monte_carlo() fallback
N_SIMULATIONS_API = 200         # backend GET /api/predictions
N_SIMULATIONS_DRY_RUN = 50      # main.py --dry-run smoke test
N_SIMULATIONS_API_MIN = 10      # POST /api/simulate lower bound
N_SIMULATIONS_API_MAX = 5_000   # POST /api/simulate upper bound

# Monte Carlo convergence analysis (notebooks/mc_convergence.ipynb)
CONVERGENCE_BATCH_SIZE = 500
CONVERGENCE_MAX_ITERATIONS = 50_000
CONVERGENCE_TOL = 0.001
CONVERGENCE_MIN_N = 2_000
CONVERGENCE_STABLE_BATCHES = 3
CONVERGENCE_TOP_K = 8
