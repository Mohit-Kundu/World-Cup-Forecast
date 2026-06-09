"""Tests for Monte Carlo convergence helpers."""

from __future__ import annotations

import pandas as pd

from src.convergence import build_convergence_history, estimate_stable_n
from src.simulations import MonteCarloAccumulator


class TestConvergenceHelpers:
    def test_build_convergence_history_shapes(self):
        checkpoints = [
            {
                "n_simulations": 500,
                "mean_champion_prob_top_k": 0.05,
                "median_champion_prob_all": 0.01,
                "p90_champion_prob_all": 0.03,
                "max_top_k_delta": float("inf"),
                "champion_probs": {"Brazil": 0.12, "France": 0.10},
            },
            {
                "n_simulations": 1000,
                "mean_champion_prob_top_k": 0.051,
                "median_champion_prob_all": 0.011,
                "p90_champion_prob_all": 0.031,
                "max_top_k_delta": 0.002,
                "champion_probs": {"Brazil": 0.121, "France": 0.099},
            },
        ]
        wide, long = build_convergence_history(checkpoints)
        assert len(wide) == 2
        assert set(wide.columns) >= {"n_simulations", "max_top_k_delta"}
        assert len(long) == 4

    def test_estimate_stable_n_finds_flat_region(self):
        wide = pd.DataFrame(
            {
                "n_simulations": [500, 1000, 1500, 2000, 2500],
                "max_top_k_delta": [float("inf"), 0.01, 0.0005, 0.0004, 0.0003],
            }
        )
        assert estimate_stable_n(wide, tol=0.001, min_n=2000, stable_batches=2) == 2500

    def test_estimate_stable_n_none_when_never_stable(self):
        wide = pd.DataFrame(
            {
                "n_simulations": [1000, 2000, 3000],
                "max_top_k_delta": [0.05, 0.04, 0.03],
            }
        )
        assert estimate_stable_n(wide, tol=0.001, min_n=500, stable_batches=2) is None

    def test_empty_accumulator_has_zero_sims(self):
        acc = MonteCarloAccumulator()
        assert acc.n_simulations == 0