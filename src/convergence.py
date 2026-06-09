"""
src/convergence.py
==================
Helpers for Monte Carlo convergence analysis (notebooks/mc_convergence.ipynb).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from src.config import (
    CONVERGENCE_TOL,
    CONVERGENCE_MIN_N,
    CONVERGENCE_STABLE_BATCHES,
    CONVERGENCE_TOP_K,
    WC2026_GROUPS,
)


def build_convergence_history(
    checkpoints: List[Dict[str, Any]],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Build wide (aggregate) and long (per-team) DataFrames from checkpoints."""
    if not checkpoints:
        empty_wide = pd.DataFrame(
            columns=[
                "n_simulations",
                "mean_champion_prob_top_k",
                "median_champion_prob_all",
                "p90_champion_prob_all",
                "max_top_k_delta",
            ]
        )
        empty_long = pd.DataFrame(columns=["n_simulations", "team", "champion_prob"])
        return empty_wide, empty_long

    wide_rows = []
    long_rows = []
    for cp in checkpoints:
        n = cp["n_simulations"]
        wide_rows.append(
            {
                "n_simulations": n,
                "mean_champion_prob_top_k": cp.get("mean_champion_prob_top_k"),
                "median_champion_prob_all": cp.get("median_champion_prob_all"),
                "p90_champion_prob_all": cp.get("p90_champion_prob_all"),
                "max_top_k_delta": cp.get("max_top_k_delta"),
            }
        )
        for team, prob in cp.get("champion_probs", {}).items():
            long_rows.append({"n_simulations": n, "team": team, "champion_prob": prob})

    return pd.DataFrame(wide_rows), pd.DataFrame(long_rows)


def estimate_stable_n(
    wide_history: pd.DataFrame,
    tol: float = CONVERGENCE_TOL,
    min_n: int = CONVERGENCE_MIN_N,
    stable_batches: int = CONVERGENCE_STABLE_BATCHES,
) -> Optional[int]:
    """First n where max_top_k_delta stays below tol for stable_batches checkpoints."""
    if wide_history.empty or "max_top_k_delta" not in wide_history.columns:
        return None

    df = wide_history.sort_values("n_simulations").reset_index(drop=True)
    streak = 0
    for _, row in df.iterrows():
        n = int(row["n_simulations"])
        delta = row["max_top_k_delta"]
        if n < min_n or pd.isna(delta) or delta == float("inf"):
            streak = 0
            continue
        if delta < tol:
            streak += 1
            if streak >= stable_batches:
                return n
        else:
            streak = 0
    return None


def plot_convergence(
    wide_history: pd.DataFrame,
    long_history: pd.DataFrame,
    output_path: Optional[Union[str, Path]] = None,
    top_n: int = 5,
    tol: float = CONVERGENCE_TOL,
) -> None:
    """Plot champion-prob stability and max-delta diagnostic vs iterations."""
    import matplotlib.pyplot as plt

    if wide_history.empty:
        raise ValueError("wide_history is empty - run checkpoint sweep first.")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    if not long_history.empty:
        final_n = wide_history["n_simulations"].max()
        final_probs = long_history[long_history["n_simulations"] == final_n]
        top_teams = (
            final_probs.sort_values("champion_prob", ascending=False)
            .head(top_n)["team"]
            .tolist()
        )
        for team in top_teams:
            team_series = long_history[long_history["team"] == team].sort_values(
                "n_simulations"
            )
            ax1.plot(
                team_series["n_simulations"],
                team_series["champion_prob"],
                label=team,
                linewidth=1.5,
            )

    ax1.plot(
        wide_history["n_simulations"],
        wide_history["mean_champion_prob_top_k"],
        color="black",
        linestyle="--",
        linewidth=1.2,
        label="mean (top-K)",
    )
    ax1.plot(
        wide_history["n_simulations"],
        wide_history["median_champion_prob_all"],
        color="gray",
        linestyle=":",
        linewidth=1.2,
        label="median (all teams)",
    )
    ax1.plot(
        wide_history["n_simulations"],
        wide_history["p90_champion_prob_all"],
        color="dimgray",
        linestyle="-.",
        linewidth=1.0,
        label="p90 (all teams)",
    )
    ax1.set_ylabel("P(champion)")
    ax1.set_title("Champion probability vs iterations")
    ax1.legend(loc="upper right", fontsize=8)
    ax1.grid(True, alpha=0.3)

    deltas = wide_history["max_top_k_delta"].replace(float("inf"), np.nan)
    ax2.plot(wide_history["n_simulations"], deltas, color="steelblue", linewidth=1.5)
    ax2.axhline(tol, color="red", linestyle="--", linewidth=1.0, label=f"tol={tol}")
    ax2.set_xlabel("n_simulations")
    ax2.set_ylabel("max_top_k_delta")
    ax2.set_title("Convergence diagnostic")
    ax2.legend(loc="upper right", fontsize=8)
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    if output_path is not None:
        fig.savefig(output_path, dpi=120)
    plt.show()
