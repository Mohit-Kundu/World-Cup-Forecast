import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_simulation_service
from backend.schemas.simulation import SimulationRequest
from backend.services.exceptions import SimulationValidationError
from backend.services.simulation_service import SimulationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["simulate"])


@router.post("/simulate")
async def run_custom_simulation(
    request: SimulationRequest,
    svc: SimulationService = Depends(get_simulation_service),
):
    """Run a custom simulation with specified number of iterations."""
    try:
        result = svc.run_custom(request.n_simulations)
        return {**result, "source": "live"}
    except SimulationValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in custom simulation: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e
