"""
main.py
=======
FIFA World Cup 2026 Prediction Pipeline — Main Entrypoint

Usage:
  python main.py                          # Full run (N=10,000)
  python main.py --n-simulations 100      # Quick test run
  python main.py --dry-run                # Validate pipeline (N=50, no output)
  python main.py --skip-training          # Load saved models (faster re-runs)
  python main.py --data-dir path/to/data  # Custom data directory

Output:
  submission.csv     — competition submission file
  models/            — serialised model artifacts
  champion_probs.csv — team win probabilities
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import RANDOM_SEED

# Set all random seeds for reproducibility
np.random.seed(RANDOM_SEED)

# ---------------------------------------------------------------------------
# Logging Setup (UTF-8 safe for Windows)
# ---------------------------------------------------------------------------

_fmt = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)

# Stream handler: use errors='replace' to safely handle non-cp1252 chars
_stream_handler = logging.StreamHandler(sys.stdout)
_stream_handler.setFormatter(_fmt)
if hasattr(_stream_handler.stream, "reconfigure"):
    try:
        _stream_handler.stream.reconfigure(errors="replace")
    except Exception:
        pass  # Older Python / non-reconfigurable streams

# File handler: always UTF-8
_file_handler = logging.FileHandler("pipeline.log", mode="w", encoding="utf-8")
_file_handler.setFormatter(_fmt)

logging.basicConfig(level=logging.INFO, handlers=[_stream_handler, _file_handler])
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pipeline Imports
# ---------------------------------------------------------------------------

from src.preprocessing import load_and_preprocess
from src.feature_engineering import build_feature_matrix
from src.models import train_all_models, save_models, load_models
from src.simulations import run_monte_carlo
from src.helpers import format_submission


# ---------------------------------------------------------------------------
# Argument Parser
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="FIFA World Cup 2026 Prediction Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Path to the data directory containing CSVs",
    )
    parser.add_argument(
        "--n-simulations",
        type=int,
        default=10_000,
        help="Number of Monte Carlo simulation iterations",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline with N=50 simulations (validation only, no output written)",
    )
    parser.add_argument(
        "--skip-training",
        action="store_true",
        help="Skip training and load saved models from models/ directory",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="submission.csv",
        help="Output path for the submission CSV",
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default="models",
        help="Directory for saving/loading model artifacts",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Validation Helpers
# ---------------------------------------------------------------------------

def validate_features(df_features: pd.DataFrame) -> None:
    """Asserts the feature matrix has no NaNs before training."""
    from src.feature_engineering import FEATURE_COLS
    nan_counts = df_features[FEATURE_COLS].isna().sum()
    n_nan_cols = (nan_counts > 0).sum()
    if n_nan_cols > 0:
        logger.warning(f"[WARN] {n_nan_cols} feature column(s) contain NaN values -- check preprocessing.")
    else:
        logger.info("[OK]  Feature matrix: no NaN values found.")

    logger.info(f"[OK]  Feature matrix shape: {df_features.shape}")
    logger.info(f"[OK]  Training samples: {len(df_features):,}")


def validate_submission(df_submission: pd.DataFrame) -> None:
    """Asserts the submission file has expected structure."""
    required_cols = [
        "match_id", "stage", "home_team", "away_team",
        "predicted_home_goals", "predicted_away_goals",
        "home_win_prob", "draw_prob", "away_win_prob",
    ]
    missing = [c for c in required_cols if c not in df_submission.columns]
    if missing:
        logger.error(f"[ERR] Submission missing columns: {missing}")
    else:
        logger.info(f"[OK]  Submission structure valid: {len(df_submission)} matches")

    # Check probabilities sum to ~1
    prob_sum = (
        df_submission["home_win_prob"]
        + df_submission["draw_prob"]
        + df_submission["away_win_prob"]
    )
    off = (prob_sum - 1.0).abs() > 0.01
    if off.any():
        logger.warning(f"[WARN] {off.sum()} match(es) have probabilities not summing to 1.0")
    else:
        logger.info("[OK]  All match probabilities sum to 1.0")


# ---------------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    if args.dry_run:
        args.n_simulations = 50
        logger.info("DRY RUN mode: N=50 simulations, output will not be written.")

    logger.info("=" * 70)
    logger.info("  FIFA WORLD CUP 2026 — PREDICTION PIPELINE")
    logger.info("=" * 70)
    logger.info(f"  Data dir:    {args.data_dir}")
    logger.info(f"  Simulations: {args.n_simulations:,}")
    logger.info(f"  Output:      {args.output}")
    logger.info("=" * 70)

    t_start = time.time()

    # ------------------------------------------------------------------
    # STEP 1: Preprocessing
    # ------------------------------------------------------------------
    logger.info("\n[STEP 1/4] Loading and preprocessing data...")
    t0 = time.time()

    df_matches, team_hist, elo_dict = load_and_preprocess(args.data_dir)

    logger.info(f"  Preprocessing complete in {time.time() - t0:.1f}s")
    logger.info(f"  Matches loaded: {len(df_matches):,}")
    logger.info(f"  Teams in history: {len(team_hist)}")

    # ------------------------------------------------------------------
    # STEP 2: Feature Engineering
    # ------------------------------------------------------------------
    logger.info("\n[STEP 2/4] Building feature matrix...")
    t0 = time.time()

    df_features = build_feature_matrix(df_matches, team_hist)
    validate_features(df_features)

    logger.info(f"  Feature engineering complete in {time.time() - t0:.1f}s")

    # ------------------------------------------------------------------
    # STEP 3: Model Training
    # ------------------------------------------------------------------
    if args.skip_training:
        logger.info("\n[STEP 3/4] Loading saved models (--skip-training)...")
        models = load_models(args.model_dir)
    else:
        logger.info("\n[STEP 3/4] Training models...")
        t0 = time.time()
        models = train_all_models(df_features)
        logger.info(f"  Training complete in {time.time() - t0:.1f}s")
        save_models(models, args.model_dir)

    # ------------------------------------------------------------------
    # STEP 4: Monte Carlo Simulation
    # ------------------------------------------------------------------
    logger.info(f"\n[STEP 4/4] Running Monte Carlo simulation (N={args.n_simulations:,})...")
    t0 = time.time()

    mc_output = run_monte_carlo(
        team_hist=team_hist,
        elo_df=elo_dict,
        models=models,
        n_simulations=args.n_simulations,
    )

    logger.info(f"  Monte Carlo complete in {time.time() - t0:.1f}s")

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    if not args.dry_run:
        df_submission = format_submission(mc_output["match_results"])
        validate_submission(df_submission)

        output_path = Path(args.output)
        df_submission.to_csv(output_path, index=False)
        logger.info(f"\n[OK]  Submission saved -> {output_path.resolve()}")

        # Save champion probabilities
        champ_df = pd.DataFrame(
            [
                {"team": team, "win_probability": prob}
                for team, prob in sorted(
                    mc_output["champion_probs"].items(), key=lambda x: -x[1]
                )
            ]
        )
        champ_path = Path("champion_probs.csv")
        champ_df.to_csv(champ_path, index=False)
        logger.info(f"[OK]  Champion probabilities saved -> {champ_path.resolve()}")

        # Save finalist probabilities
        finalist_df = pd.DataFrame(
            [
                {"team": team, "finalist_probability": prob}
                for team, prob in sorted(
                    mc_output["finalist_probs"].items(), key=lambda x: -x[1]
                )
            ]
        )
        finalist_df.to_csv("finalist_probs.csv", index=False)
        logger.info(f"[OK]  Finalist probabilities saved -> finalist_probs.csv")

    else:
        logger.info("\n[OK]  DRY RUN complete -- pipeline executed without errors.")

    logger.info(f"\n{'='*70}")
    logger.info(f"  Total runtime: {time.time() - t_start:.1f}s")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    main()
