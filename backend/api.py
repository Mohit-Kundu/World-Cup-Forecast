"""
FastAPI Backend for FIFA World Cup 2026 Prediction Frontend
============================================================
Serves model predictions and team statistics via REST API.

Endpoints:
  - GET /api/predictions: Full Monte Carlo simulation results
  - POST /api/simulate: Custom simulation with configurable iterations
  - GET /health: Health check endpoint
"""

from contextlib import asynccontextmanager
from functools import lru_cache
import logging
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.config import (
    OUTPUT_DIR,
    N_SIMULATIONS_API,
    N_SIMULATIONS_API_MIN,
    N_SIMULATIONS_API_MAX,
)
from src.models import load_models
from src.predictions_io import (
    build_team_stats,
    format_predictions_response,
    load_predictions_json,
    predictions_json_path,
)
from src.preprocessing import load_and_preprocess
from src.simulations import run_monte_carlo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load models; skip MC warm-up when pipeline snapshot exists."""
    logger.info("Pre-warming API resources...")
    get_resources()

    if predictions_json_path(OUTPUT_DIR).is_file():
        logger.info("Found output/predictions.json — skipping MC warm-up.")
    else:
        logger.info("No pipeline snapshot — warming default simulation cache...")
        run_simulation_cached(n_simulations=N_SIMULATIONS_API)
        get_team_stats_cached()

    logger.info("API warm-up complete.")
    yield


# Initialize FastAPI app
app = FastAPI(
    title="FIFA WC 2026 Prediction API",
    description="ML-powered predictions for FIFA World Cup 2026",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global cache for loaded resources
_cached_resources = None


def get_resources():
    """Load and cache ML models and historical data."""
    global _cached_resources
    if _cached_resources is None:
        logger.info("Loading models and data...")
        data_dir = Path(__file__).parent.parent / "data"
        model_dir = Path(__file__).parent.parent / "models"

        df_matches, team_hist, elo_dict = load_and_preprocess(str(data_dir))
        models = load_models(str(model_dir))

        _cached_resources = {
            "df_matches": df_matches,
            "team_hist": team_hist,
            "elo_dict": elo_dict,
            "models": models,
        }
        logger.info("Resources loaded successfully!")
    return _cached_resources


@lru_cache(maxsize=10)
def get_team_stats_cached(n_simulations: int = N_SIMULATIONS_API):
    """Calculate and cache team base statistics."""
    resources = get_resources()
    return build_team_stats(resources["team_hist"], resources["elo_dict"])


@lru_cache(maxsize=10)
def run_simulation_cached(n_simulations: int = N_SIMULATIONS_API):
    """Run Monte Carlo simulation and cache results."""
    resources = get_resources()
    logger.info(f"Running Monte Carlo simulation with {n_simulations} iterations...")

    mc_results = run_monte_carlo(
        team_hist=resources["team_hist"],
        elo_df=resources["elo_dict"],
        models=resources["models"],
        n_simulations=n_simulations,
    )

    logger.info("Simulation complete!")
    return mc_results


class SimulationRequest(BaseModel):
    n_simulations: int = N_SIMULATIONS_API


@app.get("/")
async def root():
    """Landing page for the API — the React app runs separately on port 5173."""
    return {
        "service": "FIFA WC 2026 Prediction API",
        "status": "running",
        "message": "This is the API server. Open the React frontend at http://localhost:5173",
        "endpoints": {
            "health": "/health",
            "predictions": "/api/predictions",
            "simulate": "POST /api/simulate",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "FIFA WC 2026 Prediction API"}


@app.get("/api/predictions")
async def get_predictions():
    """
    Get full prediction results including match outcomes,
    champion probabilities, and team statistics.
    """
    try:
        cached = load_predictions_json(OUTPUT_DIR)
        if cached is not None:
            return {**cached, "source": "pipeline"}

        mc_results = run_simulation_cached(n_simulations=N_SIMULATIONS_API)
        team_stats = get_team_stats_cached(n_simulations=N_SIMULATIONS_API)

        return {
            **format_predictions_response(mc_results, team_stats, N_SIMULATIONS_API),
            "source": "live",
        }
    except Exception as e:
        logger.error(f"Error generating predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/simulate")
async def run_custom_simulation(request: SimulationRequest):
    """
    Run a custom simulation with specified number of iterations.
    """
    try:
        if (
            request.n_simulations < N_SIMULATIONS_API_MIN
            or request.n_simulations > N_SIMULATIONS_API_MAX
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"n_simulations must be between "
                    f"{N_SIMULATIONS_API_MIN} and {N_SIMULATIONS_API_MAX}"
                ),
            )

        mc_results = run_simulation_cached(n_simulations=request.n_simulations)
        team_stats = get_team_stats_cached(n_simulations=request.n_simulations)

        return {
            **format_predictions_response(
                mc_results, team_stats, request.n_simulations
            ),
            "source": "live",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in custom simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting FastAPI server...")
    get_resources()

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
