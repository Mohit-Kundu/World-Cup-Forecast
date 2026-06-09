"""
train_models.py
===============
Train and save ML models without running Monte Carlo simulations.

Usage:
  python train_models.py
  python train_models.py --data-dir data --model-dir models
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import numpy as np

from src.config import RANDOM_SEED, OUTPUT_DIR
from src.preprocessing import load_and_preprocess
from src.feature_engineering import load_or_build_feature_matrix, FEATURE_COLS
from src.models import train_all_models, save_models

np.random.seed(RANDOM_SEED)

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

_fmt = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)

_stream_handler = logging.StreamHandler(sys.stdout)
_stream_handler.setFormatter(_fmt)
if hasattr(_stream_handler.stream, "reconfigure"):
    try:
        _stream_handler.stream.reconfigure(errors="replace")
    except Exception:
        pass

_file_handler = logging.FileHandler(
    Path(OUTPUT_DIR) / "train_models.log", mode="w", encoding="utf-8"
)
_file_handler.setFormatter(_fmt)

logging.basicConfig(level=logging.INFO, handlers=[_stream_handler, _file_handler])
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train FIFA WC 2026 prediction models (no simulation)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Path to the data directory containing CSVs",
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default="models",
        help="Directory for saving model artifacts",
    )
    return parser.parse_args()


def validate_features(df_features) -> None:
    nan_counts = df_features[FEATURE_COLS].isna().sum()
    n_nan_cols = (nan_counts > 0).sum()
    if n_nan_cols > 0:
        logger.warning(
            f"[WARN] {n_nan_cols} feature column(s) contain NaN values — check preprocessing."
        )
    else:
        logger.info("[OK]  Feature matrix: no NaN values found.")

    logger.info(f"[OK]  Feature matrix shape: {df_features.shape}")
    logger.info(f"[OK]  Training samples: {len(df_features):,}")


def main() -> None:
    args = parse_args()

    logger.info("=" * 70)
    logger.info("  FIFA WC 2026 — MODEL TRAINING ONLY")
    logger.info("=" * 70)
    logger.info(f"  Data dir:  {args.data_dir}")
    logger.info(f"  Model dir: {args.model_dir}")
    logger.info("=" * 70)

    t_start = time.time()

    logger.info("\n[STEP 1/3] Loading and preprocessing data...")
    t0 = time.time()
    df_matches, team_hist, _elo_dict = load_and_preprocess(args.data_dir)
    logger.info(f"  Done in {time.time() - t0:.1f}s")
    logger.info(f"  Matches loaded: {len(df_matches):,}")
    logger.info(f"  Teams in history: {len(team_hist)}")

    logger.info("\n[STEP 2/3] Building feature matrix...")
    t0 = time.time()
    df_features = load_or_build_feature_matrix(
        df_matches, team_hist, data_dir=args.data_dir
    )
    validate_features(df_features)
    logger.info(f"  Done in {time.time() - t0:.1f}s")

    logger.info("\n[STEP 3/3] Training models...")
    t0 = time.time()
    models = train_all_models(df_features)
    save_models(models, args.model_dir)
    logger.info(f"  Done in {time.time() - t0:.1f}s")

    model_path = Path(args.model_dir).resolve()
    logger.info(f"\n[OK]  Models saved -> {model_path}")
    logger.info(f"\n{'=' * 70}")
    logger.info(f"  Total runtime: {time.time() - t_start:.1f}s")
    logger.info(f"{'=' * 70}")


if __name__ == "__main__":
    main()
