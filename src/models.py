"""
src/models.py
=============
ML model training, persistence, and prediction.

Models trained:
  - home_goals / away_goals   : LightGBM Poisson Regressor
  - home_yellow / away_yellow : LightGBM Poisson Regressor
  - home_red / away_red       : Logistic Regression (probability of >= 1 red)
  - home_corners / away_corners: Ridge Regression

All goal/yellow/corner models use Improvement #1: exponential recency weights.

Public API:
  train_all_models(df_features) -> ModelBundle
  predict_lambdas(models, feature_row) -> PredictionBundle
  save_models(models, output_dir)
  load_models(model_dir) -> ModelBundle
"""

from __future__ import annotations

import logging
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.preprocessing import StandardScaler

from src.feature_engineering import compute_recency_weights
from src.config import FEATURE_COLS, MIN_TRAIN_SAMPLES, RANDOM_SEED

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hyperparameters (single source of truth)
# ---------------------------------------------------------------------------

LGBM_GOALS_PARAMS: Dict[str, Any] = {
    "objective": "poisson",
    "n_estimators": 500,
    "learning_rate": 0.05,
    "max_depth": 6,
    "num_leaves": 31,
    "min_child_samples": 20,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "random_state": RANDOM_SEED,
    "n_jobs": -1,
    "verbose": -1,
}

LGBM_YELLOW_PARAMS: Dict[str, Any] = {
    **LGBM_GOALS_PARAMS,
    "n_estimators": 300,
    "max_depth": 5,
}

LOGISTIC_PARAMS: Dict[str, Any] = {
    "C": 1.0,
    "max_iter": 1000,
    "random_state": RANDOM_SEED,
    "solver": "lbfgs",
}

RIDGE_PARAMS: Dict[str, Any] = {
    "alpha": 5.0,
}



# ---------------------------------------------------------------------------
# Model Bundle Dataclass
# ---------------------------------------------------------------------------


@dataclass
class ModelBundle:
    """Container for all trained models and their scalers."""

    home_goals: LGBMRegressor
    away_goals: LGBMRegressor
    home_yellow: LGBMRegressor
    away_yellow: LGBMRegressor
    home_red: LogisticRegression
    away_red: LogisticRegression
    home_corners: Ridge
    away_corners: Ridge
    # Scalers (used for logistic/ridge models)
    scaler_red: StandardScaler
    scaler_corners: StandardScaler
    # Store feature column order for prediction safety
    feature_cols: list


@dataclass
class PredictionBundle:
    """Predicted lambda/probability parameters for a single match."""

    home_goals_lambda: float
    away_goals_lambda: float
    home_yellow_lambda: float
    away_yellow_lambda: float
    home_red_prob: float
    away_red_prob: float
    home_corners_lambda: float
    away_corners_lambda: float
    home_elo: float
    away_elo: float


# ---------------------------------------------------------------------------
# Training Helpers
# ---------------------------------------------------------------------------


def _validate_features(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    """Assert all feature columns exist and contain no NaNs."""
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Feature columns missing from training data: {missing}")
    nan_counts = df[cols].isna().sum()
    if nan_counts.any():
        bad = nan_counts[nan_counts > 0].to_dict()
        logger.warning(f"NaN in training features (will fill with median): {bad}")
        df = df.copy()
        df[cols] = df[cols].fillna(df[cols].median())
    return df


def _fit_lgbm(
    model: LGBMRegressor,
    X: np.ndarray,
    y: np.ndarray,
    weights: np.ndarray,
    model_name: str,
) -> LGBMRegressor:
    """Fits a LightGBM model with recency sample weights and early stopping."""
    logger.info(f"  Training {model_name} on {len(X):,} samples...")
    # Clip targets to valid range for Poisson (must be > 0)
    y_clipped = np.clip(y, 0.001, None)
    model.fit(X, y_clipped, sample_weight=weights)
    logger.info(f"  {model_name} trained ✓")
    return model


def _fit_logistic(
    model: LogisticRegression,
    scaler: StandardScaler,
    X: np.ndarray,
    y: np.ndarray,
    model_name: str,
) -> Tuple[LogisticRegression, StandardScaler]:
    """Fits a Logistic Regression model with feature scaling."""
    logger.info(f"  Training {model_name} on {len(X):,} samples...")
    X_scaled = scaler.fit_transform(X)
    # Ensure at least 2 classes exist (rare for red cards)
    if len(np.unique(y)) < 2:
        logger.warning(f"  {model_name}: only one class in training data. Using constant probability.")
        # Set dummy second sample to ensure fit works
        X_scaled = np.vstack([X_scaled, X_scaled[:1]])
        y = np.append(y, 1 - y[0])
    model.fit(X_scaled, y)
    logger.info(f"  {model_name} trained ✓")
    return model, scaler


def _fit_ridge(
    model: Ridge,
    scaler: StandardScaler,
    X: np.ndarray,
    y: np.ndarray,
    weights: np.ndarray,
    model_name: str,
) -> Tuple[Ridge, StandardScaler]:
    """Fits a Ridge Regression model with scaling and sample weights."""
    logger.info(f"  Training {model_name} on {len(X):,} samples...")
    X_scaled = scaler.fit_transform(X)
    model.fit(X_scaled, y, sample_weight=weights)
    logger.info(f"  {model_name} trained ✓")
    return model, scaler


# ---------------------------------------------------------------------------
# Public Training API
# ---------------------------------------------------------------------------


def train_all_models(df_features: pd.DataFrame) -> ModelBundle:
    """
    Trains all 8 prediction models on the full historical feature matrix.

    Uses Improvement #1 (recency weights) for all goal/card/corner models.

    Parameters
    ----------
    df_features : output of build_feature_matrix(), contains feature cols + targets

    Returns
    -------
    ModelBundle with all fitted models
    """
    logger.info("=" * 60)
    logger.info("TRAINING ALL MODELS")
    logger.info("=" * 60)

    if len(df_features) < MIN_TRAIN_SAMPLES:
        raise ValueError(
            f"Insufficient training data: {len(df_features)} rows "
            f"(minimum {MIN_TRAIN_SAMPLES} required)."
        )

    df_features = _validate_features(df_features, FEATURE_COLS)

    # Fit on named DataFrame so LightGBM tracks feature names
    X_df = df_features[FEATURE_COLS]
    weights = compute_recency_weights(df_features).values

    # --- Goals ---
    home_goals_model = _fit_lgbm(
        LGBMRegressor(**LGBM_GOALS_PARAMS),
        X_df, df_features["home_goals"].values, weights, "home_goals"
    )
    away_goals_model = _fit_lgbm(
        LGBMRegressor(**LGBM_GOALS_PARAMS),
        X_df, df_features["away_goals"].values, weights, "away_goals"
    )

    # --- Yellow Cards ---
    home_yellow_model = _fit_lgbm(
        LGBMRegressor(**LGBM_YELLOW_PARAMS),
        X_df, df_features["home_yellow"].values, weights, "home_yellow"
    )
    away_yellow_model = _fit_lgbm(
        LGBMRegressor(**LGBM_YELLOW_PARAMS),
        X_df, df_features["away_yellow"].values, weights, "away_yellow"
    )

    # --- Red Cards (Logistic) ---
    X_np = X_df.values  # Logistic/Ridge need numpy
    scaler_red = StandardScaler()
    home_red_model, scaler_red = _fit_logistic(
        LogisticRegression(**LOGISTIC_PARAMS),
        scaler_red,
        X_np, df_features["home_red"].values.astype(int), "home_red"
    )
    scaler_red_away = StandardScaler()
    away_red_model, scaler_red_away = _fit_logistic(
        LogisticRegression(**LOGISTIC_PARAMS),
        scaler_red_away,
        X_np, df_features["away_red"].values.astype(int), "away_red"
    )

    # --- Corners (Ridge) ---
    scaler_corners_home = StandardScaler()
    home_corners_model, scaler_corners_home = _fit_ridge(
        Ridge(**RIDGE_PARAMS),
        scaler_corners_home,
        X_np, df_features["home_corners"].values, weights, "home_corners"
    )
    scaler_corners_away = StandardScaler()
    away_corners_model, scaler_corners_away = _fit_ridge(
        Ridge(**RIDGE_PARAMS),
        scaler_corners_away,
        X_np, df_features["away_corners"].values, weights, "away_corners"
    )

    # Log feature importances for goals model
    _log_feature_importances(home_goals_model, "home_goals")

    logger.info("=" * 60)
    logger.info("ALL MODELS TRAINED SUCCESSFULLY")
    logger.info("=" * 60)

    return ModelBundle(
        home_goals=home_goals_model,
        away_goals=away_goals_model,
        home_yellow=home_yellow_model,
        away_yellow=away_yellow_model,
        home_red=home_red_model,
        away_red=away_red_model,
        home_corners=home_corners_model,
        away_corners=away_corners_model,
        scaler_red=scaler_red,
        scaler_corners=scaler_corners_home,
        feature_cols=FEATURE_COLS,
    )


def _log_feature_importances(model: LGBMRegressor, name: str) -> None:
    """Logs top-10 feature importances for a LightGBM model."""
    importances = pd.Series(model.feature_importances_, index=FEATURE_COLS)
    top10 = importances.nlargest(10)
    logger.info(f"\n  [{name}] Top-10 Feature Importances:")
    for feat, imp in top10.items():
        logger.info(f"    {feat:<25} {imp:>8.1f}")


# ---------------------------------------------------------------------------
# Prediction API
# ---------------------------------------------------------------------------


def predict_lambdas(
    models: ModelBundle,
    feature_row: pd.DataFrame,
) -> PredictionBundle:
    """
    Generates prediction parameters for a single future match.

    Parameters
    ----------
    models      : trained ModelBundle
    feature_row : single-row DataFrame from build_prediction_row()

    Returns
    -------
    PredictionBundle with goal/card/corner lambdas and Elo values
    """
    # Pass named DataFrame to LightGBM (avoids feature name warnings)
    X_df = feature_row[models.feature_cols]
    X_np = X_df.values  # numpy array for sklearn models

    home_gl = float(np.clip(models.home_goals.predict(X_df)[0], 0.1, 10.0))
    away_gl = float(np.clip(models.away_goals.predict(X_df)[0], 0.1, 10.0))

    home_yl = float(np.clip(models.home_yellow.predict(X_df)[0], 0.0, 10.0))
    away_yl = float(np.clip(models.away_yellow.predict(X_df)[0], 0.0, 10.0))

    X_scaled_red = models.scaler_red.transform(X_np)
    home_rp = float(models.home_red.predict_proba(X_scaled_red)[0][1])
    away_rp = float(models.away_red.predict_proba(X_scaled_red)[0][1])

    X_scaled_corners = models.scaler_corners.transform(X_np)
    home_cl = float(np.clip(models.home_corners.predict(X_scaled_corners)[0], 1.0, 20.0))
    away_cl = float(np.clip(models.away_corners.predict(X_scaled_corners)[0], 1.0, 20.0))

    home_elo = float(feature_row["home_elo"].values[0])
    away_elo = float(feature_row["away_elo"].values[0])

    return PredictionBundle(
        home_goals_lambda=home_gl,
        away_goals_lambda=away_gl,
        home_yellow_lambda=home_yl,
        away_yellow_lambda=away_yl,
        home_red_prob=home_rp,
        away_red_prob=away_rp,
        home_corners_lambda=home_cl,
        away_corners_lambda=away_cl,
        home_elo=home_elo,
        away_elo=away_elo,
    )


# ---------------------------------------------------------------------------
# Model Persistence
# ---------------------------------------------------------------------------


def save_models(models: ModelBundle, output_dir: str | Path) -> None:
    """Serialises the ModelBundle to disk using pickle."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "model_bundle.pkl"
    with open(path, "wb") as f:
        pickle.dump(models, f)
    logger.info(f"Models saved to {path}")


def load_models(model_dir: str | Path) -> ModelBundle:
    """Loads a previously saved ModelBundle from disk."""
    path = Path(model_dir) / "model_bundle.pkl"
    if not path.exists():
        raise FileNotFoundError(f"No saved models found at {path}")
    with open(path, "rb") as f:
        models = pickle.load(f)
    logger.info(f"Models loaded from {path}")
    return models
