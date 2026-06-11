import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_prediction_service
from backend.services.exceptions import PredictionsNotFoundError
from backend.services.prediction_service import PredictionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


@router.get("/status")
async def get_predictions_status(
    svc: PredictionService = Depends(get_prediction_service),
):
    """Check if predictions.json snapshot exists and return its metadata."""
    try:
        return svc.get_status()
    except Exception as e:
        logger.error("Error checking predictions status: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("")
async def get_predictions(
    svc: PredictionService = Depends(get_prediction_service),
):
    """
    Get full prediction results from predictions.json snapshot.
    Does NOT run simulations - returns 404 if no snapshot exists.
    Use POST /api/simulate to run live simulations.
    """
    try:
        return {**svc.get_predictions(), "source": "pipeline"}
    except PredictionsNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error loading predictions: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e
