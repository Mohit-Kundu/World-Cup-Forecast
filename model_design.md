# FIFA World Cup 2026 — Prediction Model Design Document

## 1. Architecture Overview

The pipeline is structured as a **multi-stage ML forecasting + Monte Carlo simulation system**. Each stage is a self-contained Python module with a single responsibility.

```
data/ (raw CSVs)
  └─> preprocessing.py   (clean, standardise, build team history)
        └─> feature_engineering.py  (build ML feature matrix per match)
              └─> models.py         (train 8 models: goals, yellows, reds, corners)
                    └─> simulations.py  (Monte Carlo tournament simulation)
                          └─> submission.csv
```

---

## 2. Design Principles

### 2.1 Modularity
Each pipeline stage is an independent module (`src/`). Stages communicate via clean dataclass interfaces (`MatchRecord`) and DataFrames. No notebook-specific state is shared between stages.

### 2.2 Reproducibility
- All random seeds are set explicitly via `RANDOM_SEED = 42`.
- Monte Carlo iterations are parameterised (`N_SIMULATIONS`).
- Model hyperparameters are defined in one place (`src/models.py`).

### 2.3 Robustness
- Feature engineering handles cold-start teams (< 5 matches) with linear interpolation.
- NaN guards are applied before every `.fit()` call.
- All division operations use `.clip(lower=1e-6)` to prevent zero-division.

### 2.4 Extensibility
- Adding a new feature only requires updating `add_match_features()`.
- Adding a new model only requires a new entry in `MODELS` dict in `models.py`.
- Simulation logic is decoupled from bracket definitions (easily swap WC fixtures).

---

## 3. Feature Engineering

### 3.1 Core Features

| Feature | Description | Source |
|---------|-------------|--------|
| `elo_diff` | Home Elo − Away Elo | `elo.csv` |
| `home_attack` | Weighted rolling goals scored (last 10 games) | `history_stat.csv` |
| `home_defense` | Weighted rolling goals conceded (last 10 games) | `history_stat.csv` |
| `away_attack` | Same for away team | `history_stat.csv` |
| `away_defense` | Same for away team | `history_stat.csv` |
| `tournament_weight` | Importance multiplier by competition type | `history_stat.csv` |
| `is_host` | 1 if home team is USA/Canada/Mexico playing at home | constant |

### 3.2 Improvement Features

| Feature | Description | Improvement # |
|---------|-------------|---------------|
| `home_recent_form` | Points/game in last 5 matches, scaled [0,1] | #2 |
| `away_recent_form` | Same for away team | #2 |
| `h2h_win_rate` | Home team win rate vs away team (last 15 yrs) | #3 |
| `h2h_goal_diff` | Average goal diff in H2H (last 15 yrs) | #3 |
| `home_discipline` | Data-driven yellow card proxy from conceded goals | #4 |
| `away_discipline` | Same for away team | #4 |

---

## 4. Machine Learning Models

### 4.1 Goals Models (home_goals, away_goals)
- **Algorithm:** LightGBM `LGBMRegressor` with `objective='poisson'`
- **Rationale:** Goal counts are non-negative integers following a Poisson distribution. LightGBM's Poisson objective directly optimises log-likelihood of the Poisson distribution, outperforming standard regression objectives for count data.
- **Sample Weights:** Exponential decay with 15-year half-life (Improvement #1)

### 4.2 Yellow Card Models (home_yellow, away_yellow)
- **Algorithm:** LightGBM `LGBMRegressor` with `objective='poisson'`
- **Rationale:** Same distributional assumption as goals. Card counts are small non-negative integers.
- **Target:** Dynamic discipline proxy (`compute_dynamic_discipline`) replacing static lookup.
- **Sample Weights:** Same recency weighting as goals models.

### 4.3 Red Card Models (home_red, away_red)
- **Algorithm:** `LogisticRegression` (sklearn)
- **Rationale:** Red cards are rare binary events (0 or ≥1). Modelling as a classification probability is more calibrated than regression.
- **Target:** `(discipline_proxy > 3.0).astype(int)` as a binary threshold proxy.

### 4.4 Corner Models (home_corners, away_corners)
- **Algorithm:** `Ridge` regression (sklearn)
- **Rationale:** Corner counts are continuous-ish and symmetric enough for linear regression. Ridge regularisation prevents overfitting on the noisy synthetic proxy.
- **Sample Weights:** Same recency weighting.

---

## 5. Tournament Simulation

### 5.1 Match-Level Simulation
Each simulated match draws outcomes from:
- Goals: `Poisson(λ_goals)` — λ from LightGBM model
- Yellow cards: `Poisson(λ_yellow)` — λ from LightGBM model  
- Red cards: `Bernoulli(p_red)` — p from Logistic Regression
- Corners: `Poisson(λ_corners)` — λ from Ridge model (rounded)

### 5.2 Extra Time & Penalties
- Extra time: simulated with 0.8 expected goals, split proportionally by team λ ratios
- Penalties (Improvement #5): Elo-calibrated sigmoid probability clipped to [0.35, 0.65]
  ```
  P(home wins) = sigmoid(elo_diff / 400), clipped to [0.35, 0.65]
  ```

### 5.3 Group Stage Tiebreakers
FIFA official order: **Points → GD → GF → Yellow Cards → Red Cards → Random**

### 5.4 Monte Carlo Aggregation
- Default: N=10,000 iterations
- Most common scoreline wins each match slot
- Win probability = frequency of advancing / N

---

## 6. Improvements Summary

| # | Improvement | Problem Solved | Impact |
|---|-------------|----------------|--------|
| 1 | Recency Weighting | Old matches dilute modern signal | High |
| 2 | Rolling Form Features | Momentum not captured | Medium |
| 3 | H2H Features | Rivalry dynamics ignored | Medium |
| 4 | Dynamic Discipline Proxy | Hardcoded for only 34 teams | High |
| 5 | Elo-Calibrated Penalties | Flat 50/50 is unrealistic | Medium |

---

## 7. Running the Pipeline

```bash
# Install dependencies
pip install -r requirements.txt

# Run full pipeline (N=10,000 simulations)
python main.py

# Quick test run (N=100)
python main.py --n-simulations 100 --dry-run
```

Output: `submission.csv` in the project root.
