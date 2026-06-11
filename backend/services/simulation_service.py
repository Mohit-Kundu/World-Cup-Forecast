import logging
from functools import lru_cache

from src.config import N_SIMULATIONS_API_MAX, N_SIMULATIONS_API_MIN
from src.predictions_io import build_team_stats, format_predictions_response
from src.simulations import run_monte_carlo

from backend.services.exceptions import SimulationValidationError
from backend.services.resource_service import ResourceService

logger = logging.getLogger(__name__)


class SimulationService:
    """Run Monte Carlo simulations using cached ML resources."""

    def __init__(self, resource_service: ResourceService) -> None:
        self._resource_service = resource_service
        self._get_team_stats = lru_cache(maxsize=10)(self._compute_team_stats)
        self._run_simulation = lru_cache(maxsize=10)(self._compute_simulation)

    def _compute_team_stats(self, n_simulations: int) -> dict:
        del n_simulations  # cache key only; stats do not depend on iteration count
        resources = self._resource_service.get()
        return build_team_stats(resources["team_hist"], resources["elo_dict"])

    def _compute_simulation(self, n_simulations: int) -> dict:
        resources = self._resource_service.get()
        logger.info(
            "Running Monte Carlo simulation with %s iterations...", n_simulations
        )
        mc_results = run_monte_carlo(
            team_hist=resources["team_hist"],
            elo_df=resources["elo_dict"],
            models=resources["models"],
            n_simulations=n_simulations,
        )
        logger.info("Simulation complete!")
        return mc_results

    def run_custom(self, n_simulations: int) -> dict:
        if (
            n_simulations < N_SIMULATIONS_API_MIN
            or n_simulations > N_SIMULATIONS_API_MAX
        ):
            raise SimulationValidationError(
                f"n_simulations must be between "
                f"{N_SIMULATIONS_API_MIN} and {N_SIMULATIONS_API_MAX}"
            )

        mc_results = self._run_simulation(n_simulations)
        team_stats = self._get_team_stats(n_simulations)

        return format_predictions_response(mc_results, team_stats, n_simulations)
