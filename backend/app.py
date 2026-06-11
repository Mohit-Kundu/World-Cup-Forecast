import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path for src imports
sys.path.append(str(Path(__file__).parent.parent))

from backend.dependencies import get_resource_service
from backend.routers import health_router, predictions_router, simulate_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load models and data only; simulations run on demand via endpoints."""
    logger.info("Pre-loading API resources...")
    get_resource_service().preload()
    logger.info("API ready.")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="FIFA WC 2026 Prediction API",
        description="ML-powered predictions for FIFA World Cup 2026",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(predictions_router)
    app.include_router(simulate_router)

    return app
