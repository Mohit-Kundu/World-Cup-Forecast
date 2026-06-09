"""
src/cache_utils.py
==================
Disk cache helpers for expensive pipeline artifacts.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from src.config import FEATURE_CACHE_DIR, MIN_MATCH_YEAR, RANDOM_SEED

logger = logging.getLogger(__name__)

_DATA_FILES = ("history_stat.csv", "elo.csv", "former_names.csv")


def compute_data_fingerprint(data_dir: Path) -> str:
    """Hash data file mtimes/sizes + pipeline constants for cache invalidation."""
    h = hashlib.md5()
    for fname in _DATA_FILES:
        path = data_dir / fname
        if path.exists():
            stat = path.stat()
            h.update(f"{fname}:{stat.st_mtime_ns}:{stat.st_size}".encode())
        else:
            h.update(f"{fname}:missing".encode())
    h.update(f"min_year={MIN_MATCH_YEAR}".encode())
    h.update(f"seed={RANDOM_SEED}".encode())
    h.update(b"v2")  # bump when feature logic changes
    return h.hexdigest()[:16]


def feature_matrix_cache_path(data_dir: Path, fingerprint: str) -> Path:
    return Path(FEATURE_CACHE_DIR) / f"feature_matrix_{fingerprint}.parquet"


def load_cached_feature_matrix(cache_path: Path) -> Optional[pd.DataFrame]:
    if not cache_path.exists():
        return None
    try:
        df = pd.read_parquet(cache_path)
        logger.info("Loaded cached feature matrix from %s (shape %s)", cache_path, df.shape)
        return df
    except Exception as exc:
        logger.warning("Failed to load feature cache %s: %s", cache_path, exc)
        return None


def save_feature_matrix_cache(df: pd.DataFrame, cache_path: Path) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache_path, index=False)
    logger.info("Saved feature matrix cache -> %s", cache_path)
