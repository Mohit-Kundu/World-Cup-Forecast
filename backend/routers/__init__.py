from backend.routers.health import router as health_router
from backend.routers.predictions import router as predictions_router
from backend.routers.simulate import router as simulate_router

__all__ = ["health_router", "predictions_router", "simulate_router"]
